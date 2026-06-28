from django.core.management.base import BaseCommand

from conditions.alerts import send_due_alerts


class Command(BaseCommand):
    help = "Send due snorkel condition email alerts"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Do not send email")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Send even when ALERT_EMAILS_ENABLED is false",
        )

    def handle(self, *args, **options):
        result = send_due_alerts(dry_run=options["dry_run"], force=options["force"])
        self.stdout.write(
            self.style.SUCCESS(
                "Checked {checked}, matched {matched}, sent {sent}, skipped {skipped}".format(
                    **result
                )
            )
        )
