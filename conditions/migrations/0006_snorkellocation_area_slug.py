from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("conditions", "0005_forecasthour_country_time_index"),
    ]

    operations = [
        migrations.AddField(
            model_name="snorkellocation",
            name="area_slug",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Optional parent area/hub slug, e.g. maui for Maui beach spots",
                max_length=64,
            ),
        ),
    ]
