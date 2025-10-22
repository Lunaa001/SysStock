from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('AccountAdmin', '0003_auto_20250429_2041'),
        ('SysstockApp', "0005_alter_branch_options"),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='sucursal',
            field=models.ForeignKey(
                to='SysstockApp.branch',
                related_name='usuarios',
                on_delete=django.db.models.deletion.PROTECT,
                null=True, blank=True,   # lo ponemos nullable para no romper al crear la columna
            ),
        ),
    ]
