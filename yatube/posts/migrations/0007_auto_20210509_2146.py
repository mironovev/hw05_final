# Generated by Django 2.2.6 on 2021-05-09 18:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_comment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-pub_date', 'id']},
        ),
    ]