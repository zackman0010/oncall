from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import GrafanaAPIPermission, LegacyAccessControlRole, get_most_authorized_role
from apps.public_api.urls import router


@pytest.mark.parametrize(
    "rbac_enabled,role,give_perm",
    [
        # rbac disabled: we will check the role is enough based on get_most_authorized_role for the perm
        (False, "admin", None),
        (False, "editor", None),
        (False, "viewer", None),
        (False, None, None),
        # rbac enabled: having role None, check the perm is required
        (True, None, False),
        (True, None, True),
    ],
)
@pytest.mark.django_db
def test_rbac_permissions(
    make_organization_and_user_with_token,
    rbac_enabled,
    role,
    give_perm,
):
    # APIView default actions
    # (name, http method, detail-based)
    default_actions = {
        "create": ("post", False),
        "list": ("get", False),
        "retrieve": ("get", True),
        "update": ("put", True),
        "partial_update": ("patch", True),
        "destroy": ("delete", True),
    }

    organization, user, token = make_organization_and_user_with_token()
    if organization.is_rbac_permissions_enabled != rbac_enabled:
        # skip if the organization's rbac_enabled is not the expected by the test
        return

    client = APIClient()
    # check all actions for all public API viewsets
    for _, viewset, _basename in router.registry:
        if viewset.__name__ == "ActionView":
            # old actions (webhooks) are deprecated, no RBAC support
            continue
        for viewset_method_name, required_perms in viewset.rbac_permissions.items():
            # setup user's role and permissions
            if rbac_enabled:
                # set the user's role to None and assign the permission or not based on the flag
                user.role = LegacyAccessControlRole.NONE
                user.permissions = []
                expected = status.HTTP_403_FORBIDDEN
                if give_perm:
                    # if permissions are given, expect a 200 response
                    user.permissions = [GrafanaAPIPermission(action=perm.value) for perm in required_perms]
                    expected = status.HTTP_200_OK
                user.save()
            else:
                # set the user's role to the given role
                user.role = LegacyAccessControlRole[role.upper()] if role else LegacyAccessControlRole.NONE
                user.save()
                # check what the minimum required role for the perms is
                required_role = get_most_authorized_role(required_perms)
                # set expected depending on the user's role
                expected = status.HTTP_200_OK if user.role <= required_role else status.HTTP_403_FORBIDDEN

            # iterate over all viewset actions, making an API request for each,
            # using the user's token and confirming the response status code
            if viewset_method_name in default_actions:
                http_method, detail = default_actions[viewset_method_name]
            else:
                action_method = getattr(viewset, viewset_method_name)
                http_method = list(action_method.mapping.keys())[0]
                detail = action_method.detail

            method_path = f"{viewset.__module__}.{viewset.__name__}.{viewset_method_name}"
            success = Response(status=status.HTTP_200_OK)
            kwargs = {"pk": "NONEXISTENT"} if detail else None
            if viewset_method_name in default_actions and detail:
                url = reverse(f"api-public:{_basename}-detail", kwargs=kwargs)
            elif viewset_method_name in default_actions and not detail:
                url = reverse(f"api-public:{_basename}-list", kwargs=kwargs)
            else:
                name = viewset_method_name.replace("_", "-")
                url = reverse(f"api-public:{_basename}-{name}", kwargs=kwargs)

            with patch(method_path, return_value=success):
                response = client.generic(path=url, method=http_method, HTTP_AUTHORIZATION=token)
                assert response.status_code == expected
