from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ForecastHour",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("country_slug", models.CharField(max_length=64)),
                ("city_slug", models.CharField(max_length=64)),
                ("time", models.DateTimeField()),
                ("ok", models.BooleanField(default=False)),
                ("score", models.FloatField(default=0.0)),
                ("rating", models.CharField(max_length=16)),
                ("wave_height", models.FloatField(blank=True, null=True)),
                ("wind_speed", models.FloatField(blank=True, null=True)),
                ("sea_surface_temperature", models.FloatField(blank=True, null=True)),
                ("sea_level_height", models.FloatField(blank=True, null=True)),
                ("current_velocity", models.FloatField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddConstraint(
            model_name="forecasthour",
            constraint=models.UniqueConstraint(
                fields=("country_slug", "city_slug", "time"), name="uniq_location_time"
            ),
        ),
        migrations.AddIndex(
            model_name="forecasthour",
            index=models.Index(
                fields=["country_slug", "city_slug", "time"],
                name="conditions_country_city_time_idx",
            ),
        ),
    ]
