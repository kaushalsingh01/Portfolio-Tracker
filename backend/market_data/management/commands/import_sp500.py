from django.core.management.base import BaseCommand
from market_data.models import Stock
import pandas as pd
import yfinance as yf
import requests
from io import StringIO
import os

class Command(BaseCommand):
    help = "Import S&P 500 stock list using yfinance, with optional caching"

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh',
            action='store_true',
            help='Refresh the cached S&P 500 list from Wikipedia'
        )

    @staticmethod
    def fetch_sp500_table():
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return pd.read_html(StringIO(response.text), header=0)[0]

    def handle(self, *args, **options):
        cache_file = "sp500_companies.csv"
        use_cache = not options["refresh"]

        self.stdout.write("Loading S&P 500 tickers...")

        try:
            if use_cache and os.path.exists(cache_file):
                table = pd.read_csv(cache_file)
                self.stdout.write(self.style.NOTICE("Loaded tickers from cache."))
            else:
                table = self.fetch_sp500_table()
                table.to_csv(cache_file, index=False)
                self.stdout.write(self.style.SUCCESS("Fetched tickers from Wikipedia and cached."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to load tickers: {e}"))
            return

        symbols = table["Symbol"].tolist()
        added, skipped = 0, 0

        for symbol in symbols:
            try:
                info = yf.Ticker(symbol).info
                company_name = info.get("shortName", symbol)
                sector = info.get("sector", "")

                obj, created = Stock.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        "company_name": company_name,
                        "sector": sector,
                    }
                )
                if created:
                    added += 1
                else:
                    skipped += 1

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Skipped {symbol}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Import complete: Added {added}, Skipped {skipped}."))