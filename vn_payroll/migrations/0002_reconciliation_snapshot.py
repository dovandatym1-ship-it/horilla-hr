"""Append-only audit snapshots for Vietnam payroll reconciliation (NOT payment)."""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("vn_payroll", "0001_initial"),
        ("employee", "0009_alter_actiontype_is_active_and_more"),
        ("payroll", "0012_alter_allowance_is_active_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="VNPayrollReconciliationSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("source_sha256", models.CharField(max_length=64)),
                ("input_sha256", models.CharField(max_length=64)),
                ("record_sha256", models.CharField(max_length=64, unique=True)),
                ("rule_version", models.PositiveIntegerField()),
                ("result_exact", models.DecimalField(decimal_places=6, max_digits=24)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("company", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="vn_payroll_reconciliation_snapshots",
                    to="base.company")),
                ("employee", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="vn_payroll_reconciliation_snapshots",
                    to="employee.employee")),
                ("contract", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="vn_payroll_reconciliation_snapshots",
                    to="payroll.contract")),
                ("rule", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="reconciliation_snapshots",
                    to="vn_payroll.formularule")),
                ("actor", models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name="vn_payroll_reconciliation_snapshots",
                    to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at", "-pk"],
                "permissions": [
                    ("record_vnpayrollreconciliationsnapshot",
                     "Can record Vietnam payroll reconciliation evidence")
                ],
            },
        ),
    ]
