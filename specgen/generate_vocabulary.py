#!/usr/bin/env python

import click
import csv as csv_engine
import tempfile
import os
from lxml import etree as ET
from entry import get_supported_schemas, voc_to_spec, \
    voc_to_spec_from_rdf, csv_catalog_to_ap, merge_rdf, contributor_to_rdf

SUPPORTED_SCHEMAS = get_supported_schemas()


@click.command()
@click.option('--rdf', '-r',
              type=click.Path(exists=True, resolve_path=True),
              help='Path to Vocabulary RDF file (.ttl/.rdf/.json/.jsonld/.nt/.nq/.n3)')
@click.option('--rdf_contributor',
              type=click.Path(exists=True, resolve_path=True),
              help='Path to Author RDF file (.ttl/.rdf/.json/.jsonld/.nt/.nq/.n3)')
@click.option('--csv_contributor',
              type=click.Path(exists=True, resolve_path=True),
              help='Path to Author CSV file (.csv)')
@click.option('--csv', '-c',
              type=click.Path(exists=True, resolve_path=True),
              help='Path to Author or Application Profile CSV file (.csv)')
@click.option('--output', '-o', type=click.File('wb'),
              help='Name of output file')
@click.option('--ap', is_flag=True,
              help='Output full AP instead of vocabulary')
@click.option('--contributors', is_flag=True,
              help='Output RDF of authors, editors and contributors')
@click.option('--merge', is_flag=True,
              help='Merge RDF of vocabulary RDF with RDF of authors')
@click.option('--csv_contributor_role_column',
              help='Column name containing roles in the contributor CSV file .'
                   'Also used to form the ontology namespace for the contributors command.')
@click.option('--title', help='Title of the AP')
@click.option('--schema', '-s',
              help='Metadata schema')
@click.option('--schema_folder',
              type=click.Path(exists=True, resolve_path=True,
                              dir_okay=True, file_okay=False),
              help='Directory containing additional templates.')
def process_args(rdf, rdf_contributor, csv_contributor, csv, ap, contributors,
                 merge, csv_contributor_role_column, schema, schema_folder, output, title):
    xml_output = False

    if not ap and not contributors and not merge:
        if rdf is None:
            raise click.UsageError('Missing arguments input RDF --rdf {path}')

        # Convert the RDF vocabulary to html
        schema = schema or 'vocabularynlv2.j2'
        xml_output = voc_to_spec(rdf, schema, schema_folder=schema_folder)

    elif ap:
        if not title:
            raise click.UsageError('Missing argument --title')

        if not csv and not rdf:
            raise click.UsageError('Missing argument --csv or --rdf')

        if not csv and rdf:
            # Convert the RDF to a CSV catalog file
            csv_output = voc_to_spec_from_rdf(rdf, title)
            xp = tempfile.mkdtemp()
            xp = os.path.join(xp, title)
            with open(xp, 'w') as csvfile:
                writer = csv_engine.DictWriter(csvfile, fieldnames=csv_output.pop(0))
                writer.writeheader()
                for row in csv_output:
                    writer.writerow(row)

            csv = os.path.realpath(xp)

        # Render the CSV catalog file using the template
        schema = schema or 'ap.j2'
        xml_output = csv_catalog_to_ap(csv, schema, title, csv_contributor=csv_contributor,
                               csv_column=csv_contributor_role_column, schema_folder=schema_folder)

    elif contributors:
        if csv is None:
            raise click.UsageError('Missing arguments --csv')
        if csv_contributor_role_column is None:
            raise click.UsageError('Missing arguments --csv_contributor_role_column {column}')
        # Renders the contributors CSV to RDF
        schema = schema or 'contributors.j2'
        xml_output = contributor_to_rdf(csv, csv_contributor_role_column, schema, schema_folder=schema_folder)

    elif merge:
        if rdf is None:
            raise click.UsageError('Missing arguments --rdf')
        if rdf_contributor is None:
            raise click.UsageError('Missing arguments --rdf_contributors')

        merged = merge_rdf(rdf, rdf_contributor)
        if output is None:
            click.echo_via_pager(merged)
        else:
            output.write(merged)

    if xml_output:
        if output is None:
            # Write to console
            click.echo_via_pager(ET.tostring(xml_output.getroot()))
        else:
            # Write to specified file
            if not os.path.exists(os.path.dirname(output.name)):
                os.makedirs(os.path.dirname(output.name))
            xml_output.write(output)


if __name__ == '__main__':
    process_args()
