from django.core.management.base import BaseCommand

from tools.models import Tool


class Command(BaseCommand):
    help = "Create default tools (Facebook Bulk Post Remover)."

    def handle(self, *args, **options):
        tool, created = Tool.objects.get_or_create(
            slug="facebook-bulk-post-remover",
            defaults={
                "name": "Facebook Bulk Post Remover",
                "description": "Select posts from your connected Page and delete them in bulk. 1 credit per successful delete.",
                "is_published": True,
                "is_hidden": False,
                "is_in_maintenance": False,
                "sort_order": 10,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created tool: {tool.slug}"))
        else:
            self.stdout.write(f"Tool already exists: {tool.slug}")
