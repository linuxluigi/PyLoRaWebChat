import time

from django.core.management.base import BaseCommand, CommandError

from pylorawebchat.chat.lora_daemon import Daemon


class Command(BaseCommand):
    help = "start lora daemon"

    def handle(self, *args, **options):
        daemon: Daemon = Daemon()

        while True:
            try:
                time.sleep(60)
            except KeyboardInterrupt:
                print("Stop lora daemon...")
                daemon.stop()
                raise
