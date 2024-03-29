# Generated by Django 3.0.6 on 2020-05-09 02:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Swell',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('height', models.DecimalField(decimal_places=2, max_digits=4)),
                ('period', models.DecimalField(decimal_places=2, max_digits=4)),
                ('direction', models.DecimalField(decimal_places=2, max_digits=5)),
            ],
        ),
        migrations.CreateModel(
            name='TestModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('number', models.DecimalField(decimal_places=2, max_digits=4)),
                ('timestamp', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Tide',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField()),
                ('height', models.DecimalField(decimal_places=2, max_digits=4)),
                ('type', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='SurfSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('spotName', models.CharField(max_length=100)),
                ('surflineId', models.CharField(max_length=100)),
                ('timeIn', models.DateTimeField()),
                ('timeOut', models.DateTimeField()),
                ('waveCount', models.IntegerField()),
                ('surfScore', models.IntegerField()),
                ('crowdScore', models.CharField(max_length=20)),
                ('board', models.CharField(max_length=100)),
                ('swells', models.ManyToManyField(to='surfinfo.Swell')),
                ('tides', models.ManyToManyField(to='surfinfo.Tide')),
            ],
        ),
    ]
