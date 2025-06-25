import requests
from django.core.management.base import BaseCommand
from users.models import Country, State

class Command(BaseCommand):
    help = 'Fetch and store states for all countries from CountriesNow API'

    def handle(self, *args, **kwargs):
        url = "https://countriesnow.space/api/v0.1/countries/states"
        response = requests.get(url)

        if response.status_code != 200:
            self.stderr.write("Failed to fetch states")
            return

        data = response.json()

        for country_data in data['data']:
            country_name = country_data['name']
            states = country_data.get('states', [])

            try:
                country = Country.objects.get(name__iexact=country_name)
            except Country.DoesNotExist:
                self.stderr.write(f"Country not found: {country_name}")
                continue
            
            for state_data in states:
                state_name = state_data.get('name')
                if state_name:
                    State.objects.update_or_create(
                        country=country,
                        name=state_name
                    )
            self.stdout.write(f"Synced states for {country_name}")
