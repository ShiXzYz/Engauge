# Generated manually to add Course/Enrollment/Profile and link to existing models
from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion
import uuid
from django.conf import settings


def gen_join_code(apps, schema_editor):
    import random, string
    Course = apps.get_model('polls', 'Course')
    for c in Course.objects.all():
        if not c.join_code:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            # Ensure uniqueness is best-effort here
            c.join_code = code
            c.save(update_fields=['join_code'])


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0002_exit_tickets_and_kind'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('professor','Professor'),('student','Student')], max_length=20)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('join_code', models.CharField(max_length=12, unique=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses_created', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('role', models.CharField(choices=[('student','Student'),('professor','Professor')], default='student', max_length=20)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='polls.course')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user','course')}
            }
        ),
        migrations.AddField(
            model_name='document',
            name='course',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents', to='polls.course'),
        ),
        migrations.AddField(
            model_name='poll',
            name='course',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='polls', to='polls.course'),
        ),
        migrations.AddField(
            model_name='exitticket',
            name='course',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='exit_tickets', to='polls.course'),
        ),
    ]
