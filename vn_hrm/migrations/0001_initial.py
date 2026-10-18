# Initial Vietnam HRM extension models. No existing Horilla tables are altered.
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("base", "0001_initial"),
        ("employee", "0001_initial"),
        ("payroll", "0001_initial"),
        ("leave", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VNEmployeeLegalProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nationality", models.CharField(default="VN", max_length=2)),
                ("citizen_id_suffix", models.CharField(blank=True, max_length=4)),
                ("citizen_id_vault_ref", models.CharField(blank=True, max_length=200)),
                ("tax_id_suffix", models.CharField(blank=True, max_length=4)),
                ("tax_id_vault_ref", models.CharField(blank=True, max_length=200)),
                ("social_insurance_suffix", models.CharField(blank=True, max_length=4)),
                ("social_insurance_vault_ref", models.CharField(blank=True, max_length=200)),
                ("residency_type", models.CharField(choices=[("unverified", "Chưa xác minh"), ("resident", "Cư trú"), ("nonresident", "Không cư trú")], default="unverified", max_length=20)),
                ("verification_status", models.CharField(choices=[("pending", "Chưa xác minh"), ("verified", "Đã xác minh")], default="pending", max_length=20)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="base.company")),
                ("employee", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="vn_legal_profile", to="employee.employee")),
            ],
            options={"verbose_name": "Hồ sơ pháp lý nhân viên Việt Nam", "verbose_name_plural": "Hồ sơ pháp lý nhân viên Việt Nam"},
        ),
        migrations.CreateModel(
            name="VNDependent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=200)),
                ("relationship", models.CharField(max_length=40)),
                ("birth_date", models.DateField(blank=True, null=True)),
                ("identity_suffix", models.CharField(blank=True, max_length=4)),
                ("identity_vault_ref", models.CharField(blank=True, max_length=200)),
                ("eligible_from", models.DateField()),
                ("eligible_to", models.DateField(blank=True, null=True)),
                ("verification_status", models.CharField(choices=[("pending", "Chưa xác minh"), ("verified", "Đã xác minh"), ("rejected", "Không hợp lệ")], default="pending", max_length=20)),
                ("evidence_ref", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="base.company")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vn_dependents", to="employee.employee")),
            ],
            options={"verbose_name": "Người phụ thuộc", "verbose_name_plural": "Người phụ thuộc"},
        ),
        migrations.CreateModel(
            name="VNContractAmendment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amendment_code", models.CharField(max_length=64)),
                ("effective_date", models.DateField()),
                ("new_monthly_wage_vnd", models.DecimalField(decimal_places=0, max_digits=17)),
                ("status", models.CharField(choices=[("draft", "Nháp"), ("approved", "Đã duyệt")], default="draft", max_length=20)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="base.company")),
                ("contract", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="vn_amendments", to="payroll.contract")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Phụ lục hợp đồng Việt Nam",
                "verbose_name_plural": "Phụ lục hợp đồng Việt Nam",
            },
        ),
        migrations.CreateModel(
            name="VNAttendanceCorrection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("work_date", models.DateField()),
                ("requested_minutes", models.IntegerField()),
                ("reason", models.TextField()),
                ("status", models.CharField(choices=[("pending", "Chờ duyệt"), ("approved", "Đã duyệt"), ("rejected", "Đã từ chối")], default="pending", max_length=20)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="base.company")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="employee.employee")),
                ("requested_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Đề nghị điều chỉnh chấm công", "verbose_name_plural": "Đề nghị điều chỉnh chấm công"},
        ),
        migrations.CreateModel(
            name="VNLeaveLedgerEntry",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source_key", models.CharField(max_length=120)),
                ("effective_date", models.DateField()),
                ("units", models.DecimalField(decimal_places=2, max_digits=9)),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="base.company")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="employee.employee")),
                ("leave_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="leave.leavetype")),
            ],
            options={
                "verbose_name": "Giao dịch số dư phép",
                "verbose_name_plural": "Giao dịch số dư phép",
                "ordering": ("effective_date", "created_at"),
            },
        ),
        migrations.AddConstraint(
            model_name="vncontractamendment",
            constraint=models.UniqueConstraint(fields=("company", "amendment_code"), name="vn_contract_amendment_code_unique"),
        ),
        migrations.AddConstraint(
            model_name="vnleaveledgerentry",
            constraint=models.UniqueConstraint(fields=("company", "source_key"), name="vn_leave_ledger_source_unique"),
        ),
    ]
