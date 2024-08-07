# Generated by Django 4.2.11 on 2024-07-04 20:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0051_remove_escalationpolicy_custom_button_trigger'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channelfilter',
            name='filtering_term_type',
            field=models.IntegerField(choices=[(0, 'regex'), (1, 'jinja2'), (2, 'labels')], default=0),
        ),
    ]