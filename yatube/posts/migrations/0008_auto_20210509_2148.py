# Generated by Django 2.2.6 on 2021-05-09 18:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0007_auto_20210509_2146'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-created', 'id']},
        ),
        migrations.RenameField(
            model_name='comment',
            old_name='pub_date',
            new_name='created',
        ),
    ]
