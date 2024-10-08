# Generated by Django 3.2.15 on 2024-06-21 21:56

from django.db import migrations, models
from django.db.models import F
import django.utils.timezone
from specifyweb.businessrules.exceptions import BusinessRuleException
from specifyweb.specify.models import (
    protect_with_blockers,
    Collectionobject,
    Collectionobjecttype,
    Collection,
    Discipline,
    Institution,
    Picklist,
    Picklistitem,
    Taxontreedef
)
from specifyweb.specify.update_schema_config import (
    update_table_schema_config_with_defaults,
    revert_table_schema_config,
)

# Migrations Operations Order:
# 1. Create CollectionObjectType
# 2. Add CollectionObjectType (coType) realtionship to CollectionObject
# 3. Add hasreferencecatalognumber field to CollectionObject
# 4. Create default collection object types based on each discipline
# 5. Create new default taxon trees and ranks
# 6. Create CollectionObjectGroup
# 7. Create CollectionObjectGroupJoin
# 8. Add discipline relationship to TreeDef tables
# 9. Add schema config for new sp7 tables

SCHEMA_CONFIG_TABLES = [
    ('CollectionObjectType', None),
    ('CollectionObjectGroupType', None),
    ('CollectionObjectGroup', None),
    ('CollectionObjectGroupJoin', None),
    ('SpUserExternalId', 'Stores provider identifiers and tokens for users who sign in using Single Sign On (SSO).'),
    ('SpAttachmentDataSet', 'Holds attachment data sets.'),
    ('UniquenessRule', 'Stores table names in the data model that have uniqueness rules configured for each discipline.'),
    ('UniquenessRuleField', 'Stores field names in the data model that have uniqueness rules configured for each discipline, linked to UniquenessRule records.'),
    ('Message', 'Stores user notifications.'),
    ('SpMerging', 'Tracks record and task IDs of records being merged.'),
    ('UserPolicy', 'Records permissions for a user within a collection.'),
    ('UserRole', 'Records roles associated with ecify users.'),
    ('Role', 'Stores names, descriptions, and collection information for user-created roles.'),
    ('RolePolicy', 'Stores resource and action permissions for user-created roles within a collection.'),
    ('LibraryRole', 'Stores names and descriptions of default roles that can be added to any collection.'),
    ('LibraryRolePolicy', 'Stores resource and action permissions for library roles within a collection.'),
    ('SpDataSet', 'Stores Specify Data Sets created during bulk import using the WorkBench, typically through spreadsheet uploads.')
]

DEFAULT_COG_TYPES = [
    'Discrete',
    'Consolidated',
    'Drill Core',
]

def create_default_collection_types():
    # Create default collection types for each collection, named after the discipline
    for collection in Collection.objects.all():
        discipline = collection.discipline
        discipline_name = discipline.name
        cot, created = Collectionobjecttype.objects.get_or_create(
            name=discipline_name,
            collection=collection,
            taxontreedef_id=discipline.taxontreedef_id
        )
        # Update CollectionObjects' collectionobjecttype for the discipline
        Collectionobject.objects.filter(collection=collection).update(collectionobjecttype=cot)
        collection.collectionobjecttype = cot
        try:
            collection.save()
        except BusinessRuleException as e:
            if str(e) == 'Collection must have unique code in discipline':
                codes = Collection.objects.filter(code=collection.code).values_list('code', flat=True)
                i = 1
                # May want to do something besides numbering, but users can edit if after the migrqation if they want.
                while True:
                    collection.code = f'{collection.code}-{i}'
                    if collection.code not in codes:
                        break
                collection.save()
            continue

def revert_default_collection_types():
    # Reverse handeled by table deletion.
    pass

def revert_default_cog_types():
    # Reverse handeled by table deletion
    pass

def create_default_discipline_for_tree_defs():
    for discipline in Discipline.objects.all():
        geography_tree_def = discipline.geographytreedef
        geography_tree_def.discipline = discipline
        geography_tree_def.save()

        geologic_time_period_tree_def = discipline.geologictimeperiodtreedef
        geologic_time_period_tree_def.discipline = discipline
        geologic_time_period_tree_def.save()

        lithostrat_tree_def = discipline.lithostrattreedef
        lithostrat_tree_def.discipline = discipline
        lithostrat_tree_def.save()

        taxon_tree_def = discipline.taxontreedef
        taxon_tree_def.discipline = discipline
        taxon_tree_def.save()

    for institution in Institution.objects.all():
        storage_tree_def = institution.storagetreedef
        storage_tree_def.institution = institution
        storage_tree_def.save()

def revert_default_discipline_for_tree_defs():
    # Reverse handeled by table deletion
    pass

def create_table_schema_config_with_defaults():
    for discipline in Discipline.objects.all():
        for table, desc in SCHEMA_CONFIG_TABLES:
            update_table_schema_config_with_defaults(table, discipline.id, discipline, desc)

def revert_table_schema_config_with_defaults():
    for table, _ in SCHEMA_CONFIG_TABLES:
        revert_table_schema_config(table)

def create_default_collection_object_types():
    for collection in Collection.objects.all():
        cog_type_picklist = Picklist.objects.create(
            name='Default Collection Object Group Types',
            tablename='Collectionobjectgrouptype',
            issystem=False,
            type=1,
            readonly=False,
            collection=collection
        )
        for cog_type in DEFAULT_COG_TYPES:
            Picklistitem.objects.create(
                title=cog_type,
                value=cog_type,
                picklist=cog_type_picklist
            )

def revert_default_collection_object_types():
    for collection in Collection.objects.all():
        cog_type_picklist_qs = Picklist.objects.filter(
            name='Default Collection Object Group Types',
            tablename='Collectionobjectgrouptype',
            collection=collection
        )
        if cog_type_picklist_qs.exists():
            cog_type_picklist = cog_type_picklist_qs.first()
            Picklistitem.objects.filter(picklist=cog_type_picklist).delete()
            cog_type_picklist.delete()

def set_discipline_for_taxon_treedefs():
    collection_object_types = Collectionobjecttype.objects.filter(
        taxontreedef__discipline__isnull=True
    ).annotate(
        discipline=F('collection__discipline')
    )

    for cot in collection_object_types:
        Taxontreedef.objects.filter(id=cot.taxontreedef_id).update(discipline=cot.discipline)

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('specify', '0001_initial'),
    ]
    
    def consolidated_python_django_migration_operations(apps, schema_editor):
        create_default_collection_types()
        create_default_discipline_for_tree_defs()
        create_table_schema_config_with_defaults()
        create_default_collection_object_types()
        set_discipline_for_taxon_treedefs()

    def revert_cosolidated_python_django_migration_operations(apps, schema_editor):
        revert_default_collection_object_types()
        revert_table_schema_config_with_defaults()
        revert_default_discipline_for_tree_defs()
        revert_default_collection_types()

    operations = [
        migrations.RunPython(consolidated_python_django_migration_operations, revert_cosolidated_python_django_migration_operations, atomic=True),
    ]
