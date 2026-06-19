from odoo import models

class AttachmentNotFound(models.TransientModel):
    _name = 'attachment.warning'

    def button_continue(self):
        return False
    def button_attach(self):
        return True

