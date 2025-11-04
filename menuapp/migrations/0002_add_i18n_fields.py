from django.db import migrations, models

def backfill_i18n(apps, schema_editor):
    # Аккуратно переложим старые значения в *_ru, если такие колонки (name/description) ещё есть в БД
    with schema_editor.connection.cursor() as c:
        for sql in [
            "UPDATE menuapp_category SET name_ru = COALESCE(NULLIF(name_ru, ''), name, '')",
            "UPDATE menuapp_category SET description_ru = COALESCE(NULLIF(description_ru, ''), description, '')",
            "UPDATE menuapp_dish SET name_ru = COALESCE(NULLIF(name_ru, ''), name, '')",
            "UPDATE menuapp_dish SET description_ru = COALESCE(NULLIF(description_ru, ''), description, '')",
        ]:
            try:
                c.execute(sql)
            except Exception:
                pass  # если старых колонок нет — ок

class Migration(migrations.Migration):
    dependencies = [
        ("menuapp", "0001_initial"),
    ]

    operations = [
        # --- Category ---
        migrations.AddField(
            model_name="category",
            name="name_ru",
            field=models.CharField("Название (RU)", max_length=100, default="", blank=True),
        ),
        migrations.AddField(
            model_name="category",
            name="name_en",
            field=models.CharField("Название (EN)", max_length=100, default="", blank=True),
        ),
        migrations.AddField(
            model_name="category",
            name="name_kk",
            field=models.CharField("Атауы (KK)", max_length=100, default="", blank=True),
        ),
        migrations.AddField(
            model_name="category",
            name="description_ru",
            field=models.TextField("Описание (RU)", default="", blank=True),
        ),
        migrations.AddField(
            model_name="category",
            name="description_en",
            field=models.TextField("Описание (EN)", default="", blank=True),
        ),
        migrations.AddField(
            model_name="category",
            name="description_kk",
            field=models.TextField("Сипаттама (KK)", default="", blank=True),
        ),

        # --- Dish ---
        migrations.AddField(
            model_name="dish",
            name="name_ru",
            field=models.CharField("Название (RU)", max_length=150, default="", blank=True),
        ),
        migrations.AddField(
            model_name="dish",
            name="name_en",
            field=models.CharField("Название (EN)", max_length=150, default="", blank=True),
        ),
        migrations.AddField(
            model_name="dish",
            name="name_kk",
            field=models.CharField("Атауы (KK)", max_length=150, default="", blank=True),
        ),
        migrations.AddField(
            model_name="dish",
            name="description_ru",
            field=models.TextField("Описание (RU)", default="", blank=True),
        ),
        migrations.AddField(
            model_name="dish",
            name="description_en",
            field=models.TextField("Описание (EN)", default="", blank=True),
        ),
        migrations.AddField(
            model_name="dish",
            name="description_kk",
            field=models.TextField("Сипаттама (KK)", default="", blank=True),
        ),

        migrations.RunPython(backfill_i18n, migrations.RunPython.noop),
    ]
