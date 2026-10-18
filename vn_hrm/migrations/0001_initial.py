# Initial migration for additive Vietnamese HRM models.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("base", "0018_alter_holidays_is_specific"),
        ("employee", "0009_alter_actiontype_is_active_and_more"),
        ("payroll", "0012_alter_allowance_is_active_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VNCompanyProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("legal_name", models.CharField(max_length=255)),
                ("tax_code", models.CharField(blank=True, max_length=32)),
                ("province_code", models.CharField(blank=True, max_length=20)),
                ("commune_code", models.CharField(blank=True, max_length=20)),
                ("wage_zone", models.CharField(blank=True, choices=[("I", "Vùng I"), ("II", "Vùng II"), ("III", "Vùng III"), ("IV", "Vùng IV")], max_length=3)),
                ("last_verified_at", models.DateTimeField(blank=True, null=True)),
                ("company", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="vn_legal_profile", to="base.company")),
            ],
        ),
        migrations.CreateModel(
            name="VNEmployeeLegalProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nationality", models.CharField(default="VN", max_length=2)),
                ("tax_residency", models.CharField(choices=[("unknown", "Chưa xác định"), ("resident", "Cư trú"), ("nonresident", "Không cư trú")], default="unknown", max_length=16)),
                ("citizen_ciphertext", models.TextField(blank=True, editable=False)),
                ("citizen_digest", models.CharField(blank=True, db_index=True, editable=False, max_length=64)),
                ("tax_ciphertext", models.TextField(blank=True, editable=False)),
                ("tax_digest", models.CharField(blank=True, editable=False, max_length=64)),
                ("insurance_ciphertext", models.TextField(blank=True, editable=False)),
                ("insurance_digest", models.CharField(blank=True, editable=False, max_length=64)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="base.company")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vn_legal_profiles", to="employee.employee")),
            ],
        ),
        migrations.CreateModel(
            name="VNDependent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("relation", models.CharField(max_length=40)),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                ("valid_from", models.DateField()),
                ("valid_to", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("draft", "Chờ bổ sung"), ("verified", "Đã xác minh"), ("invalid", "Không hợp lệ")], default="draft", max_length=10)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="base.company")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vn_dependents", to="employee.employee")),
                ("verified_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="VNContractAmendment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField()),
                ("effective_from", models.DateField()),
                ("effective_to", models.DateField(blank=True, null=True)),
                ("wage_vnd", models.DecimalField(decimal_places=0, max_digits=20)),
                ("reason", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("draft", "Nháp"), ("review", "Chờ duyệt"), ("approved", "Đã duyệt")], default="draft", max_length=10)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="base.company")),
                ("contract", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vn_amendments", to="payroll.contract")),
            ],
        ),
        migrations.CreateModel(
            name="VNLeaveLedgerEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_event_key", models.CharField(max_length=100)),
                ("event_type", models.CharField(choices=[("accrual", "Tích lũy"), ("debit", "Trừ phép"), ("credit", "Hoàn phép"), ("expiry", "Hết hạn"), ("adjustment", "Điều chỉnh")], max_length=16)),
                ("units", models.DecimalField(decimal_places=3, max_digits=9)),
                ("effective_on", models.DateField()),
                ("reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="base.company")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vn_leave_events", to="employee.employee")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="VNSensitiveAccessAudit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("purpose", models.CharField(max_length=255)),
                ("action", models.CharField(max_length=30)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="base.company")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="employee.employee")),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterModelOptions(
            name="vnemployeelegalprofile",
            options={"permissions": [("manage_vn_identifiers", "Can set encrypted Vietnamese identifiers"), ("reveal_vn_identifiers", "Can reveal encrypted Vietnamese identifiers")]},
        ),
        migrations.AddConstraint(
            model_name="vnemployeelegalprofile",
            constraint=models.UniqueConstraint(fields=("company", "employee"), name="vn_hrm_employee_company_unique"),
        ),
        migrations.AddConstraint(
            model_name="vnemployeelegalprofile",
            constraint=models.UniqueConstraint(fields=("company", "citizen_digest"), condition=~models.Q(citizen_digest=""), name="vn_hrm_citizen_digest_unique"),
        ),
        migrations.AddConstraint(
            model_name="vncontractamendment",
            constraint=models.UniqueConstraint(fields=("contract", "version"), name="vn_hrm_contract_amendment_unique"),
        ),
        migrations.AddConstraint(
            model_name="vnleaveledgerevent",
            constraint=models.UniqueConstraint(fields=("company", "source_event_key", "event_type"), name="vn_hrm_leave_event_idempotency"),
        ),
    ]
