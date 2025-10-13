class StandardizeNameMixin:
    """
    Mixin para padronizar o campo 'name' de um modelo. Remove espaços extras e aplica o formato de título (Title Case).
    """
    def clean(self):
        super().clean()
        if hasattr(self, 'name') and self.name:
            self.name = self.name.strip().title()
