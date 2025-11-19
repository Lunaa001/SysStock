from django.db import migrations, models
import django.db.models.deletion
from django.db import connection


def convert_sucursal_to_foreignkey(apps, schema_editor):
    """Convert sucursal from CharField to ForeignKey"""
    with connection.cursor() as cursor:
        # Check if column exists
        cursor.execute("""
            SELECT DATA_TYPE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'AccountAdmin_user'
            AND COLUMN_NAME = 'sucursal'
        """)
        result = cursor.fetchone()
        
        if result:
            data_type = result[0]
            # If it's a varchar/char field, drop and recreate as FK
            if data_type in ('varchar', 'char', 'text'):
                cursor.execute("ALTER TABLE AccountAdmin_user DROP COLUMN sucursal")
                cursor.execute("""
                    ALTER TABLE AccountAdmin_user
                    ADD COLUMN sucursal_id INT NULL
                """)
                cursor.execute("""
                    ALTER TABLE AccountAdmin_user
                    ADD CONSTRAINT AccountAdmin_user_sucursal_fk
                    FOREIGN KEY (sucursal_id) REFERENCES SysstockApp_branch(id)
                    ON DELETE PROTECT
                """)
        else:
            # Column doesn't exist, create it as FK
            cursor.execute("""
                ALTER TABLE AccountAdmin_user
                ADD COLUMN sucursal_id INT NULL
            """)
            cursor.execute("""
                ALTER TABLE AccountAdmin_user
                ADD CONSTRAINT AccountAdmin_user_sucursal_fk
                FOREIGN KEY (sucursal_id) REFERENCES SysstockApp_branch(id)
                ON DELETE PROTECT
            """)


def reverse_sucursal_conversion(apps, schema_editor):
    """Reverse the conversion back to CharField"""
    with connection.cursor() as cursor:
        cursor.execute("ALTER TABLE AccountAdmin_user DROP FOREIGN KEY AccountAdmin_user_sucursal_fk")
        cursor.execute("ALTER TABLE AccountAdmin_user DROP COLUMN sucursal_id")
        cursor.execute("""
            ALTER TABLE AccountAdmin_user
            ADD COLUMN sucursal VARCHAR(100) DEFAULT '' NOT NULL
        """)


class Migration(migrations.Migration):
    dependencies = [
        ('AccountAdmin', '0003_auto_20250429_2041'),
        ('SysstockApp', "0005_alter_branch_options"),
    ]

    operations = [
        migrations.RunPython(convert_sucursal_to_foreignkey, reverse_sucursal_conversion),
    ]
