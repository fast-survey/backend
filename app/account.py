from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.validation import AccountValidator


class AccountManager:
    """The manager manages creating, updating and deleting admin accounts."""

    async def __init__(self, database, survey_manager):
        """Initialize an admin manager instance."""
        self.unverified_accounts = database['accounts.unverified']
        self.verified_accounts = database['accounts.verified']
        self.configurations = database['configurations']
        self.survey_manager = survey_manager
        self.validator = AccountValidator.create()

        await self.verified_accounts.create_index(
            keys='admin_name',
            name='admin-name-index',
            unique=True,
        )
        await self.verified_accounts.create_index(
            keys='email',
            name='email-index',
            unique=True,
        )
        await self.unverified_accounts.create_index(
            keys='timestamp',
            name='timestamp-index',
            expireAfterSeconds=10*60,  # delete draft accounts after 10 mins
        )

    async def fetch(self, admin_name):
        """Return the account data corresponding to given admin name."""
        account = await self.verified_accounts.find_one(
            filter={'admin_name': admin_name},
            projection={'_id': False},
        )
        if account is None:
            raise HTTPException(404, 'admin not found')
        return account

    async def create(self, admin_name, email, password):
        """Create new admin account with some default settings."""

        # TODO create account with some default data
        # TODO validate data

        if admin_name != account_data['admin_name']:
            raise HTTPException(400, 'route/account data admin names differ')
        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')
        try:
            await self.database['accounts'].insert_one(account_data)
        except DuplicateKeyError as error:
            index = str(error).split()[7]
            att = 'admin name' if index == 'admin-name-index' else 'email'
            raise HTTPException(400, f'{att} already taken')

    async def update(self, admin_name, account_data):
        """Update existing admin account data in the database."""

        # TODO update survey names and ids when admin name is changed
        if admin_name != account_data['admin_name']:
            raise HTTPException(501, 'admin name changes not yet implemented')

        if not self.validator.validate(account_data):
            raise HTTPException(400, 'invalid account data')
        result = await self.verified_accounts.replace_one(
            filter={'admin_name': admin_name},
            replacement=account_data,
        )
        if result.matched_count == 0:
            raise HTTPException(400, 'not an existing admin account')

    async def delete(self, admin_name):
        """Delete the admin including all her surveys from the database."""
        await self.verified_accounts.delete_one({'admin_name': admin_name})
        cursor = self.configurations.find(
            filter={'admin_name': admin_name},
            projection={'_id': False, 'survey_name': True},
        )
        survey_names = [e['survey_name'] for e in await cursor.to_list(None)]
        for survey_name in survey_names:
            await self.survey_manager.delete(admin_name, survey_name)
