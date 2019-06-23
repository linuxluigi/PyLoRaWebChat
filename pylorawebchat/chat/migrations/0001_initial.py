# Generated by Django 2.1.8 on 2019-06-21 09:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(max_length=250)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('message_type', models.CharField(choices=[('i', 'incoming'), ('o', 'outgoing')], max_length=1)),
                ('instant_send', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=4, unique=True)),
                ('nick', models.CharField(blank=True, max_length=255)),
                ('first_seen', models.DateTimeField(auto_now_add=True)),
                ('last_seen', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name='message',
            name='node',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.Node'),
        ),
    ]
