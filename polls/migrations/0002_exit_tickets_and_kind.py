# Generated manually for adding exit tickets and kind field
from django.db import migrations, models
import django.utils.timezone
import uuid


def add_kind_default(apps, schema_editor):
    GeneratedQuestion = apps.get_model('polls', 'GeneratedQuestion')
    GeneratedQuestion.objects.filter(kind__isnull=True).update(kind='mcq')


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='generatedquestion',
            name='kind',
            field=models.CharField(choices=[('mcq','Multiple Choice'),('exit','Exit Ticket')], default='mcq', max_length=10),
        ),
        migrations.RunPython(add_kind_default, migrations.RunPython.noop),
        migrations.CreateModel(
            name='ExitTicket',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('prompt_text', models.TextField()),
                ('active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='ExitTicketResponse',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('answer', models.TextField()),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('ticket', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='responses', to='polls.exitticket')),
            ],
        ),
        migrations.AddIndex(
            model_name='exitticketresponse',
            index=models.Index(fields=['ticket'], name='polls_exitt_ticket_i_idx'),
        ),
    ]
