# P2P_project/routers.py

class DatabaseRouter:
    """
    A router to control all database operations on models in the
    chat application.
    """
    chat_apps = {'chat'}
    main_apps = {'MainDashboard', 'auth', 'contenttypes', 'admin', 'sessions', 'authtoken', 'token_blacklist'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.main_apps:
            return 'main_db'
        if model._meta.app_label in self.chat_apps:
            return 'chat_db'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.main_apps:
            return 'main_db'
        if model._meta.app_label in self.chat_apps:
            return 'chat_db'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # السماح بالعلاقات إذا كانت الموديلز في نفس قاعدة البيانات
        db_list = ('main_db', 'default', 'chat_db')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return obj1._state.db == obj2._state.db
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'main_db':
            return app_label in self.main_apps
        elif db == 'chat_db':
            return app_label in self.chat_apps
        elif db == 'default':
            return app_label not in self.main_apps and app_label not in self.chat_apps
        return None