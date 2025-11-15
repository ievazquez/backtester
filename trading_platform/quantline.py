"""Command-line interface for the trading platform."""

import click
import sys
from datetime import datetime
import importlib.util
import os


@click.group()
def cli():
    """QuantLine - Quantitative Trading Platform (Zipline-inspired)."""
    pass


@cli.command()
@click.option(
    '-f', '--algofile',
    type=click.Path(exists=True),
    help='The file that contains the strategy to run.'
)
@click.option(
    '-t', '--algotext',
    type=str,
    help='The strategy script to run as text.'
)
@click.option(
    '--data-frequency',
    type=click.Choice(['daily', 'hourly', 'minute']),
    default='daily',
    help='The data frequency of the simulation. [default: daily]'
)
@click.option(
    '--capital-base',
    type=float,
    default=100000.0,
    help='The starting capital for the simulation. [default: 100000.0]'
)
@click.option(
    '-s', '--start',
    type=str,
    required=True,
    help='The start date of the simulation (YYYY-MM-DD).'
)
@click.option(
    '-e', '--end',
    type=str,
    required=True,
    help='The end date of the simulation (YYYY-MM-DD).'
)
@click.option(
    '--symbols',
    type=str,
    required=True,
    help='Comma-separated list of symbols to trade (e.g., AAPL,GOOGL,MSFT).'
)
@click.option(
    '-o', '--output',
    type=click.Path(),
    default=None,
    help='The location to write the results. If not specified, prints to stdout.'
)
@click.option(
    '--commission',
    type=float,
    default=0.001,
    help='Commission rate as decimal. [default: 0.001]'
)
@click.option(
    '--slippage',
    type=float,
    default=0.0005,
    help='Slippage rate as decimal. [default: 0.0005]'
)
@click.option(
    '--data-provider',
    type=click.Choice(['yahoo', 'alphavantage', 'csv']),
    default='yahoo',
    help='Data provider to use. [default: yahoo]'
)
@click.option(
    '--csv-dir',
    type=click.Path(exists=True),
    help='Directory containing CSV data files (required if data-provider=csv).'
)
@click.option(
    '--no-cache',
    is_flag=True,
    help='Disable data caching.'
)
@click.option(
    '--plot',
    is_flag=True,
    help='Plot equity curve after backtest.'
)
@click.option(
    '--metrics-only',
    is_flag=True,
    help='Only print performance metrics (no detailed output).'
)
def run(algofile, algotext, data_frequency, capital_base, start, end,
        symbols, output, commission, slippage, data_provider, csv_dir,
        no_cache, plot, metrics_only):
    """
    Run a backtest for the given strategy.

    Example:
        quantline run -f my_strategy.py -s 2020-01-01 -e 2023-12-31 --symbols AAPL,GOOGL
    """
    try:
        # Validate inputs
        if not algofile and not algotext:
            click.echo("Error: Must specify either --algofile or --algotext", err=True)
            sys.exit(1)

        # Parse dates
        try:
            start_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
        except ValueError:
            click.echo("Error: Dates must be in YYYY-MM-DD format", err=True)
            sys.exit(1)

        # Parse symbols
        symbol_list = [s.strip() for s in symbols.split(',')]

        # Convert data frequency
        interval_map = {
            'daily': '1d',
            'hourly': '1h',
            'minute': '1m'
        }
        interval = interval_map.get(data_frequency, '1d')

        # Load strategy
        strategy = load_strategy(algofile, algotext)

        # Setup data provider
        provider = setup_data_provider(data_provider, csv_dir)

        # Import required modules
        from trading_platform.backtesting.engine import BacktestEngine

        # Create backtest engine
        click.echo("=" * 60)
        click.echo("TRADING PLATFORM BACKTEST")
        click.echo("=" * 60)
        click.echo(f"Strategy: {strategy.name}")
        click.echo(f"Symbols: {', '.join(symbol_list)}")
        click.echo(f"Period: {start_date.date()} to {end_date.date()}")
        click.echo(f"Capital: ${capital_base:,.2f}")
        click.echo(f"Data Frequency: {data_frequency}")
        click.echo("=" * 60)
        click.echo()

        engine = BacktestEngine(
            strategy=strategy,
            symbols=symbol_list,
            start_date=start_date,
            end_date=end_date,
            initial_capital=capital_base,
            data_provider=provider,
            commission=commission,
            slippage=slippage,
            use_cache=not no_cache,
            interval=interval
        )

        # Run backtest
        results = engine.run()

        # Output results
        if metrics_only:
            output_text = results.summary()
        else:
            output_text = engine.summary() + "\n\n" + results.summary()

        if output:
            with open(output, 'w') as f:
                f.write(output_text)
            click.echo(f"\nResults written to: {output}")
        else:
            click.echo("\n" + output_text)

        # Save detailed results
        if output:
            # Save equity curve
            equity_df = engine.portfolio.get_equity_curve_df()
            equity_file = output.replace('.txt', '_equity.csv')
            equity_df.to_csv(equity_file)
            click.echo(f"Equity curve saved to: {equity_file}")

            # Save trades
            trades_df = engine.get_orders_df()
            if not trades_df.empty:
                trades_file = output.replace('.txt', '_trades.csv')
                trades_df.to_csv(trades_file)
                click.echo(f"Trades saved to: {trades_file}")

        # Plot if requested
        if plot:
            click.echo("\nGenerating plots...")
            results.plot_equity_curve()

        click.echo("\n" + "=" * 60)
        click.echo("BACKTEST COMPLETE")
        click.echo("=" * 60)

    except Exception as e:
        click.echo(f"Error running backtest: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option(
    '-f', '--algofile',
    type=click.Path(exists=True),
    required=True,
    help='The file that contains the strategy to run.'
)
@click.option(
    '--broker',
    type=click.Choice(['ib', 'oanda', 'darwinex']),
    required=True,
    help='Broker to use for live trading.'
)
@click.option(
    '--symbols',
    type=str,
    required=True,
    help='Comma-separated list of symbols to trade.'
)
@click.option(
    '--paper',
    is_flag=True,
    help='Use paper trading (simulated) mode.'
)
@click.option(
    '--max-position-size',
    type=float,
    default=0.1,
    help='Maximum position size as fraction of portfolio. [default: 0.1]'
)
@click.option(
    '--max-daily-loss',
    type=float,
    default=0.05,
    help='Maximum daily loss as fraction of portfolio. [default: 0.05]'
)
@click.option(
    '--update-interval',
    type=float,
    default=1.0,
    help='Update interval in seconds. [default: 1.0]'
)
def live(algofile, broker, symbols, paper, max_position_size,
         max_daily_loss, update_interval):
    """
    Run a strategy in live trading mode.

    WARNING: This will execute real trades. Always test with --paper first!

    Example:
        trading-platform live -f my_strategy.py --broker ib --symbols AAPL --paper
    """
    try:
        # Parse symbols
        symbol_list = [s.strip() for s in symbols.split(',')]

        # Load strategy
        strategy = load_strategy(algofile, None)

        # Setup broker
        broker_adapter = setup_broker(broker, paper)

        # Import required modules
        from trading_platform.execution.engine import LiveTradingEngine

        # Create live trading engine
        click.echo("=" * 60)
        click.echo("TRADING PLATFORM LIVE TRADING")
        click.echo("=" * 60)
        click.echo(f"Strategy: {strategy.name}")
        click.echo(f"Broker: {broker.upper()} {'(PAPER)' if paper else '(LIVE)'}")
        click.echo(f"Symbols: {', '.join(symbol_list)}")
        click.echo(f"Max Position Size: {max_position_size * 100}%")
        click.echo(f"Max Daily Loss: {max_daily_loss * 100}%")
        click.echo("=" * 60)

        if not paper:
            click.echo("\n⚠️  WARNING: LIVE TRADING MODE ⚠️")
            click.echo("This will execute REAL trades with REAL money!")
            click.confirm('Are you sure you want to continue?', abort=True)

        click.echo()

        engine = LiveTradingEngine(
            strategy=strategy,
            broker=broker_adapter,
            symbols=symbol_list,
            risk_manager_config={
                'max_position_size': max_position_size,
                'max_daily_loss': max_daily_loss,
            },
            update_interval=update_interval
        )

        # Start trading
        click.echo("Starting live trading... (Press Ctrl+C to stop)")
        engine.start()

        # Keep running until interrupted
        import time
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            click.echo("\n\nStopping live trading...")
            engine.stop()

        click.echo("Live trading stopped.")

    except Exception as e:
        click.echo(f"Error in live trading: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def load_strategy(algofile, algotext):
    """Load strategy from file or text."""
    if algofile:
        # Load from file
        spec = importlib.util.spec_from_file_location("strategy_module", algofile)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find Strategy class
        from trading_platform.core.strategy import Strategy

        for name in dir(module):
            obj = getattr(module, name)
            if isinstance(obj, type) and issubclass(obj, Strategy) and obj is not Strategy:
                return obj()

        raise ValueError("No Strategy class found in algorithm file")

    elif algotext:
        # Execute text
        namespace = {}
        exec(algotext, namespace)

        from trading_platform.core.strategy import Strategy

        for name, obj in namespace.items():
            if isinstance(obj, type) and issubclass(obj, Strategy) and obj is not Strategy:
                return obj()

        raise ValueError("No Strategy class found in algorithm text")


def setup_data_provider(provider_type, csv_dir):
    """Setup data provider."""
    if provider_type == 'yahoo':
        from trading_platform.data.providers import YahooFinanceProvider
        return YahooFinanceProvider()

    elif provider_type == 'alphavantage':
        api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
        if not api_key:
            raise ValueError("ALPHAVANTAGE_API_KEY environment variable required")

        from trading_platform.data.providers import AlphaVantageProvider
        return AlphaVantageProvider(api_key=api_key)

    elif provider_type == 'csv':
        if not csv_dir:
            raise ValueError("--csv-dir required when using CSV data provider")

        from trading_platform.data.providers import CSVDataProvider
        return CSVDataProvider(data_dir=csv_dir)

    return None


def setup_broker(broker_type, paper):
    """Setup broker adapter."""
    if broker_type == 'ib':
        from trading_platform.brokers.interactive_brokers import InteractiveBrokersAdapter

        port = 7497 if paper else 7496  # 7497=paper, 7496=live

        return InteractiveBrokersAdapter(
            host='127.0.0.1',
            port=port,
            client_id=1
        )

    elif broker_type == 'oanda':
        api_token = os.environ.get('OANDA_API_TOKEN')
        account_id = os.environ.get('OANDA_ACCOUNT_ID')

        if not api_token or not account_id:
            raise ValueError("OANDA_API_TOKEN and OANDA_ACCOUNT_ID environment variables required")

        from trading_platform.brokers.oanda import OANDAAdapter

        return OANDAAdapter(
            api_token=api_token,
            account_id=account_id,
            environment='practice' if paper else 'live'
        )

    elif broker_type == 'darwinex':
        account_id = os.environ.get('DARWINEX_ACCOUNT_ID')
        password = os.environ.get('DARWINEX_PASSWORD')

        if not account_id or not password:
            raise ValueError("DARWINEX_ACCOUNT_ID and DARWINEX_PASSWORD environment variables required")

        from trading_platform.brokers.darwinex import DarwinexAdapter

        return DarwinexAdapter(
            account_id=account_id,
            password=password,
            server='Darwinex-Demo' if paper else 'Darwinex-Live'
        )


def main():
    """Entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
