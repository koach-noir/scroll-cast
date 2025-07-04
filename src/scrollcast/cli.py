"""Command line interface for scroll-cast."""
import click
from pathlib import Path
from typing import Optional

from scrollcast.orchestrator.di_template_engine import DITemplateEngine
from scrollcast.config.config_loader import ConfigLoader
from scrollcast.dependency_injection import create_container


@click.group()
def main():
    """scroll-cast: Pure text animation generation system."""
    pass


@main.command()
@click.argument('text', type=str)
@click.option('--template', '-t', type=str, default='typewriter', help='Animation template to use')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--output', '-o', type=click.Path(), default='output.html', help='Output file path')
@click.option('--theme', type=str, help='Theme preset to use')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def generate(text: str, template: str, config: Optional[str], output: str, theme: Optional[str], verbose: bool):
    """Generate text animation from input text."""
    try:
        # Initialize dependency injection container
        container = create_container()
        
        # Load configuration
        config_loader = ConfigLoader()
        if config:
            config_data = config_loader.load_config(Path(config))
        else:
            # Use default config for template
            config_data = config_loader.load_template_config(template)
        
        # Apply theme if specified
        if theme:
            config_data = config_loader.apply_theme(config_data, theme)
        
        # Create template engine
        template_engine = DITemplateEngine(container)
        
        # Generate animation
        if verbose:
            click.echo(f"Generating {template} animation for: {text}")
            click.echo(f"Output: {output}")
        
        result = template_engine.generate_html(text, config_data)
        
        # Write output
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding='utf-8')
        
        if verbose:
            click.echo(f"Animation generated successfully: {output}")
        else:
            click.echo(f"Generated: {output}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@main.command()
@click.argument('text', type=str)
@click.option('--template', '-t', type=str, default='typewriter', help='Animation template to use')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--output', '-o', type=click.Path(), default='output.ass', help='Output ASS file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def subtitle(text: str, template: str, config: Optional[str], output: str, verbose: bool):
    """Generate ASS subtitle from input text."""
    try:
        # Initialize dependency injection container
        container = create_container()
        
        # Load configuration
        config_loader = ConfigLoader()
        if config:
            config_data = config_loader.load_config(Path(config))
        else:
            config_data = config_loader.load_template_config(template)
        
        # Create template engine
        template_engine = DITemplateEngine(container)
        
        # Generate ASS subtitle
        if verbose:
            click.echo(f"Generating {template} subtitle for: {text}")
            click.echo(f"Output: {output}")
        
        result = template_engine.generate_ass(text, config_data)
        
        # Write output
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding='utf-8')
        
        if verbose:
            click.echo(f"Subtitle generated successfully: {output}")
        else:
            click.echo(f"Generated: {output}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@main.command()
def templates():
    """List available animation templates."""
    template_dir = Path(__file__).parent.parent.parent / "templates"
    if template_dir.exists():
        click.echo("Available templates:")
        for template_path in template_dir.iterdir():
            if template_path.is_dir():
                click.echo(f"  - {template_path.name}")
    else:
        click.echo("No templates found")


@main.command()
@click.argument('template', type=str)
def info(template: str):
    """Show information about a specific template."""
    template_dir = Path(__file__).parent.parent.parent / "templates"
    template_path = template_dir / template
    
    if template_path.exists():
        click.echo(f"Template: {template}")
        click.echo(f"Path: {template_path}")
        
        # List available sub-templates
        sub_templates = []
        for sub_path in template_path.iterdir():
            if sub_path.is_dir():
                sub_templates.append(sub_path.name)
        
        if sub_templates:
            click.echo("Sub-templates:")
            for sub_template in sub_templates:
                click.echo(f"  - {sub_template}")
    else:
        click.echo(f"Template '{template}' not found")


if __name__ == "__main__":
    main()