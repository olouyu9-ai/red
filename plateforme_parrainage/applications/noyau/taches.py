from celery import shared_task
from .management.commands.verser_gains_quotidiens import Command

@shared_task
def verser_gains_quotidiens():
    cmd = Command()
    cmd.handle()
