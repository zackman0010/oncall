# Generated by Django 4.2.7 on 2024-01-19 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0043_remove_alertgroup_alerts_aler_channel_81aeec_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertreceivechannel',
            name='alertmanager_v2_backup_templates',
            field=models.JSONField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='alertreceivechannel',
            name='alertmanager_v2_migrated_at',
            field=models.DateTimeField(default=None, null=True),
        ),
    ]