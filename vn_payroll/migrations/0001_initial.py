# Initial migration for company-owned, versioned Vietnamese payroll formula books.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("base", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VNRuleSet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=64)),
                ("version", models.PositiveIntegerField(default=1)),
                ("title", models.CharField(max_length=200)),
                ("status", models.CharField(choices=[("draft", "Nháp"), ("review", "Chờ duyệt"), ("approved", "Đã duyệt"), ("retired", "Ngừng áp dụng")], default="draft", max_length=12)),
                ("effective_from", models.DateField()),
                ("effective_to", models.DateField(blank=True, null=True)),
                ("legal_reference", models.TextField(blank=True)),
                ("parameters", models.JSONField(blank=True, default=dict)),
                ("input_names", models.JSONField(blank=True, default=list)),
                ("golden_cases", models.JSONField(blank=True, default=list)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vn_payroll_rule_sets", to="base.company")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Bộ công thức lương Việt Nam",
                "verbose_name_plural": "Bộ công thức lương Việt Nam",
                "ordering": ("company_id", "code", "-version"),
                "permissions": [("approve_vn_ruleset", "Có quyền duyệt cấu hình lương Việt Nam")],
            },
        ),
        migrations.CreateModel(
            name="VNPayRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position", models.PositiveIntegerField(default=10)),
                ("code", models.SlugField(max_length=64)),
                ("label", models.CharField(max_length=200)),
                ("category", models.CharField(choices=[("earning", "Thu nhập"), ("subtotal", "Tổng trung gian"), ("tax", "Thuế TNCN"), ("insurance_employee", "Bảo hiểm NLĐ"), ("insurance_employer", "Bảo hiểm doanh nghiệp"), ("deduction", "Khấu trừ khác"), ("net", "Thực lĩnh")], max_length=24)),
                ("expression", models.CharField(max_length=700)),
                ("explanation", models.TextField(blank=True)),
                ("rule_set", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="vn_payroll.vnruleset")),
            ],
            options={
                "verbose_name": "Dòng công thức động",
                "verbose_name_plural": "Các dòng công thức động",
                "ordering": ("position", "pk"),
            },
        ),
        migrations.AddConstraint(
            model_name="vnruleset",
            constraint=models.UniqueConstraint(fields=("company", "code", "version"), name="vn_payroll_ruleset_version_unique"),
        ),
        migrations.AddConstraint(
            model_name="vnpayrule",
            constraint=models.UniqueConstraint(fields=("rule_set", "code"), name="vn_payrule_code_unique"),
        ),
        migrations.AddConstraint(
            model_name="vnpayrule",
            constraint=models.UniqueConstraint(fields=("rule_set", "position"), name="vn_payrule_position_unique"),
        ),
    ]
