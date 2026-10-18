# Generated migration equivalent for the initial FormulaRule model.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("base", "__first__"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FormulaRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64)),
                ("version", models.PositiveIntegerField(default=1)),
                ("title", models.CharField(max_length=255)),
                ("category", models.CharField(choices=[("earning", "Thu nhập"), ("deduction", "Khấu trừ"), ("insurance", "Bảo hiểm"), ("tax", "Thuế"), ("overtime", "Làm thêm giờ"), ("net", "Thực lĩnh")], max_length=20)),
                ("expression", models.TextField(max_length=1000)),
                ("variables", models.JSONField(default=list)),
                ("decimal_places", models.PositiveSmallIntegerField(default=0)),
                ("effective_from", models.DateField()),
                ("effective_to", models.DateField(blank=True, null=True)),
                ("legal_reference", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("draft", "Bản nháp"), ("review", "Chờ duyệt"), ("approved", "Đã duyệt"), ("retired", "Ngừng áp dụng")], default="draft", max_length=12)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="created_vn_formula_rules", to=settings.AUTH_USER_MODEL)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="approved_vn_formula_rules", to=settings.AUTH_USER_MODEL)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vn_formula_rules", to="base.company")),
            ],
            options={"ordering": ["company_id", "code", "-version"], "permissions": [("approve_formularule", "Can approve Vietnam payroll formulas"), ("preview_formularule", "Can preview Vietnam payroll formulas")]},
        ),
        migrations.AddConstraint(
            model_name="formularule",
            constraint=models.UniqueConstraint(
                fields=("company", "code", "version"),
                name="vn_formula_company_code_version_unique",
            ),
        ),
    ]
