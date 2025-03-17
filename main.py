import click
from gen_config import gen_config_inference
from run_dock import para_run_dock


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

@click.group(context_settings=CONTEXT_SETTINGS)
def dock_app():
    """Docking application, it contains the 'gen-config' and 'dock-run' sub-groups."""

dock_app.add_command(para_run_dock)
dock_app.add_command(gen_config_inference)

if __name__ == '__main__':
    dock_app()
