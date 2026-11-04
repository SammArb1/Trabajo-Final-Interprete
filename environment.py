# ENTORNO DE EJECUCIÓN (ENVIRONMENT) — almacena vinculaciones de variables y ámbitos anidados

class Environment:
    def __init__(self, outer=None):
        self.store = {}
        self.outer = outer  # ámbito padre para resolución léxica hacia arriba

    def get(self, name):
        # Búsqueda léxica encadenada: ámbito actual y asciende recursivamente
        obj = self.store.get(name)
        if obj is None and self.outer is not None:
            obj = self.outer.get(name)
        return obj

    def set(self, name, val):
        # Define una variable nueva exclusivamente en el ámbito local
        self.store[name] = val
        return val
        
    def assign(self, name, val):
        # Modifica una variable existente en el ámbito donde fue declarada originalmente
        current = self
        while current is not None:
            if name in current.store:
                current.store[name] = val
                return val
            current = current.outer
        self.store[name] = val  # fallback a asignación local si no existe previamente
        return val
