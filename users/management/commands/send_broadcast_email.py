from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from users.models import BroadcastEmail, EmailLog
from django.utils import timezone


class Command(BaseCommand):
    help = 'Send broadcast emails'

    def add_arguments(self, parser):
        parser.add_argument(
            '--broadcast-id',
            type=int,
            help='ID of the broadcast email to send',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show recipients without sending emails',
        )

    def handle(self, *args, **options):
        broadcast_id = options.get('broadcast_id')
        dry_run = options.get('dry_run', False)
        
        if not broadcast_id:
            # Show all draft broadcasts
            drafts = BroadcastEmail.objects.filter(status='draft')
            if not drafts.exists():
                self.stdout.write(self.style.WARNING('No draft broadcasts found.'))
                return
            
            self.stdout.write(self.style.SUCCESS('Draft Broadcasts:'))
            for broadcast in drafts:
                self.stdout.write(f'ID: {broadcast.id} - {broadcast.title} ({broadcast.get_recipient_type_display()})')
            
            self.stdout.write('\nUse --broadcast-id <ID> to send a specific broadcast')
            return
        
        try:
            broadcast = BroadcastEmail.objects.get(id=broadcast_id, status='draft')
        except BroadcastEmail.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Broadcast with ID {broadcast_id} not found or already sent.'))
            return
        
        # Get recipients
        recipients = list(broadcast.get_recipients())
        broadcast.total_recipients = len(recipients)
        broadcast.save()
        
        if not recipients:
            self.stdout.write(self.style.ERROR('No recipients found for this broadcast.'))
            return
        
        self.stdout.write(f'Broadcast: {broadcast.title}')
        self.stdout.write(f'Recipients: {len(recipients)} users')
        self.stdout.write(f'Type: {broadcast.get_recipient_type_display()}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n--- DRY RUN MODE ---'))
            self.stdout.write('Recipients:')
            for email in recipients[:10]:  # Show first 10
                self.stdout.write(f'  - {email}')
            if len(recipients) > 10:
                self.stdout.write(f'  ... and {len(recipients) - 10} more')
            return
        
        # Confirm sending
        confirm = input(f'\nSend email to {len(recipients)} recipients? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write('Cancelled.')
            return
        
        # Start sending
        broadcast.status = 'sending'
        broadcast.sent_at = timezone.now()
        broadcast.save()
        
        sent_count = 0
        failed_count = 0
        
        self.stdout.write(self.style.SUCCESS(f'\nSending emails...'))
        
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
                
                # Log success
                EmailLog.objects.create(
                    broadcast=broadcast,
                    recipient_email=email,
                    success=True
                )
                sent_count += 1
                
                if sent_count % 10 == 0:
                    self.stdout.write(f'Sent {sent_count}/{len(recipients)}...')
                
            except Exception as e:
                # Log failure
                EmailLog.objects.create(
                    broadcast=broadcast,
                    recipient_email=email,
                    success=False,
                    error_message=str(e)
                )
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'Failed to send to {email}: {str(e)}'))
        
        # Update broadcast status
        broadcast.emails_sent = sent_count
        broadcast.emails_failed = failed_count
        broadcast.status = 'sent' if failed_count == 0 else 'failed'
        broadcast.save()
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n--- SUMMARY ---'))
        self.stdout.write(f'Total recipients: {len(recipients)}')
        self.stdout.write(f'Emails sent: {sent_count}')
        self.stdout.write(f'Emails failed: {failed_count}')
        
        if failed_count == 0:
            self.stdout.write(self.style.SUCCESS('All emails sent successfully!'))
        else:
            self.stdout.write(self.style.WARNING(f'{failed_count} emails failed. Check EmailLog for details.'))