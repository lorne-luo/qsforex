from django.core.management.base import BaseCommand

from ...models import Trade


class Command(BaseCommand):
    help = '''print critical info of trade '''

    def add_arguments(self, parser):
        parser.add_argument('-l', '--last', type=int, help='only show last', )

    def handle(self, *args, **options):
        last = options['last'] or 0

        trades = Trade.objects.all().order_by('-id')
        if last:
            trades = trades[:last]

        trades=reversed(trades)

        print(f"Trade_id  Symbol OpenTime            Max   Pips  Min   CloseTime")
#               209463688 USDCHF 2019-09-24 01:05:06 49.60 None -21.40 2019-09-25 09:41:37
        for t in trades:
            print(t.trade_id, t.instrument.strip(), t.open_time.strftime('%Y-%m-%d %H:%M:%S'), t.max_profit, t.pips, t.min_profit, t.close_time.strftime('%Y-%m-%d %H:%M:%S'))
