from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from users.models import BroadcastEmail, EmailLog
from django.utils import timezone


class Command(BaseCommand):
    help = 'Automatically send all draft challenge broadcast emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Find all draft broadcasts for new challenges
        draft_broadcasts = BroadcastEmail.objects.filter(
            status='draft',
            title__startswith='🚩 New Challenge:'
        ).order_by('created_at')
        
        if not draft_broadcasts.exists():
            self.stdout.write(self.style.WARNING('No draft challenge broadcasts found.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {draft_broadcasts.count()} draft challenge broadcasts'))
        
        for broadcast in draft_broadcasts:
            recipients = list(broadcast.get_recipients())
            broadcast.total_recipients = len(recipients)
            broadcast.save()
            
            self.stdout.write(f'\n📧 {broadcast.title}')
            self.stdout.write(f'   Recipients: {len(recipients)} ({broadcast.get_recipient_type_display()})')
            
            if dry_run:
                self.stdout.write(self.style.WARNING('   [DRY RUN] Would send to:'))
                for email in recipients[:5]:
                    self.stdout.write(f'     - {email}')
                if len(recipients) > 5:
                    self.stdout.write(f'     ... and {len(recipients) - 5} more')
                continue
            
            if not recipients:
                self.stdout.write(self.style.WARNING('   No recipients found, skipping'))
                continue
            
            # Send emails
            broadcast.status = 'sending'
            broadcast.sent_at = timezone.now()
            broadcast.save()
            
            sent_count = 0
            failed_count = 0
            
            for email in recipients:
                try:
                    send_mail(
                        subject=broadcast.title,
                        message=broadcast.content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                        html_message=broadcast.content,
                        fail_silently=False,
                    )
                    
                    EmailLog.objects.create(
                        broadcast=broadcast,
                        recipient_email=email,
                        success=True
                    )
                    sent_count += 1
                    
                except Exception as e:
                    EmailLog.objects.create(
                        broadcast=broadcast,
                        recipient_email=email,
                        success=False,
                        error_message=str(e)
                    )
                    failed_count += 1
            
            # Update broadcast status
            broadcast.emails_sent = sent_count
            broadcast.emails_failed = failed_count
            broadcast.status = 'sent' if failed_count == 0 else 'failed'
            broadcast.save()
            
            if failed_count == 0:
                self.stdout.write(self.style.SUCCESS(f'   ✅ Sent to all {sent_count} recipients'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠️  Sent: {sent_count}, Failed: {failed_count}'))
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'\n🎉 Processed {draft_broadcasts.count()} challenge broadcasts!'))
        else:
            self.stdout.write(self.style.WARNING('\n--- DRY RUN COMPLETE ---'))
            self.stdout.write('Run without --dry-run to actually send emails')