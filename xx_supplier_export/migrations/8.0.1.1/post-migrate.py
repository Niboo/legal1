# -*- coding: utf-8 -*-


def migrate(self, cr):
    """ Clean up obsolete templates """
    cr.execute(
        """
        DELETE FROM email_template WHERE id in (
            SELECT res_id FROM ir_model_data
            WHERE module = 'xx_supplier_export'
                AND name IN (
                    'email_beekman', 'email_vedelec', 'email_aswo'));
        DELETE FROM ir_model_data
        WHERE module = 'xx_supplier_export'
            AND name IN (
                'email_beekman', 'email_vedelec', 'email_aswo');
        """
