from openerp import SUPERUSER_ID, api


def post_init_hook(cr, pool):
    """ After disabling the translatability of the locations, force
    recomputation of the 'complete name' stored function field for consistency.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    with env.manage():
        for loc in env['stock.location'].search([], order='parent_left desc'):
            loc.write({'name': loc.name})
