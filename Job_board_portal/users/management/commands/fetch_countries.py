import requests
from django.core.management.base import BaseCommand
from users.models import Country

class Command(BaseCommand):
    help = 'Fetch countries from REST Countries API and store in DB'

    def handle(self, *args, **options):
        url = 'https://restcountries.com/v3.1/all'  # Public API for countries

        response = requests.get(url)
        if response.status_code != 200:
            self.stderr.write("Failed to fetch countries")
            return

        countries = response.json()

        for country in countries:
            name = country.get('name', {}).get('common')
            cca2 = country.get('cca2')  # 2-letter country code

            if name and cca2:
                obj, created = Country.objects.update_or_create(
                    code=cca2,
                    defaults={'name': name}
                )
                if created:
                    self.stdout.write(f"Added country: {name}")
                else:
                    self.stdout.write(f"Updated country: {name}")
