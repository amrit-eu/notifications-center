import logging
import re

from alerta.exceptions import RejectException
from alerta.plugins import PluginBase
from pydantic import ValidationError

from .models.Alert_raw import Schema as AlertSchema

LOG = logging.getLogger('alerta.plugins')


class RejectPolicy(PluginBase):
    """
    Default reject policy will block alerts that do not have the following
    required attributes:
    0) Schema validation - must conform to the Alert_raw.Schema format with required
       fields: resource, event, environment, and service (non-empty set).
    1) environment - must match an allowed environment. By default it should
       be either "Production" or "Development". Config setting is `ALLOWED_ENVIRONMENTS`.
    2) service - must supply a value for service. Any value is acceptable.
    3) origin - must not match any blacklisted origins. Config setting is `ORIGIN_BLACKLIST`.
    """

    def pre_receive(self, alert, **kwargs):

        # Validate alert format against Alert_raw Schema
        try:
            # Build alert dictionary based on AlertSchema model fields
            # Extract all fields from alert object that exist in the schema
            alert_dict = {}
            for field_name in AlertSchema.model_fields.keys():
                if hasattr(alert, field_name):
                    alert_dict[field_name] = getattr(alert, field_name)


            # Validate against schema - Pydantic will:
            # - Check all required fields are present (resource, event, environment, service, attributes)
            # - Validate Attributes structure with its required fields (Country, alert_category)
            # - Validate types, enums, and all constraints
            AlertSchema(**alert_dict)
        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field_path = ' -> '.join(str(loc) for loc in error['loc'])
                error_details.append(f"{field_path}: {error['msg']}")
            error_message = '; '.join(error_details)

            LOG.warning('[POLICY] Alert validation failed: %s', error_message)
            raise RejectException(f'[POLICY] Alert does not match required schema: {error_message}')

        ORIGIN_BLACKLIST = self.get_config('ORIGIN_BLACKLIST', default=[], type=list, **kwargs)
        ALLOWED_ENVIRONMENTS = self.get_config('ALLOWED_ENVIRONMENTS', default=[], type=list, **kwargs)

        ORIGIN_BLACKLIST_REGEX = [re.compile(x) for x in ORIGIN_BLACKLIST]
        ALLOWED_ENVIRONMENT_REGEX = [re.compile(x) for x in ALLOWED_ENVIRONMENTS]

        if any(regex.match(alert.origin) for regex in ORIGIN_BLACKLIST_REGEX):
            LOG.warning("[POLICY] Alert origin '%s' has been blacklisted", alert.origin)
            raise RejectException(f"[POLICY] Alert origin '{alert.origin}' has been blacklisted")

        if not any(regex.fullmatch(alert.environment) for regex in ALLOWED_ENVIRONMENT_REGEX):
            LOG.warning('[POLICY] Alert environment does not match one of %s', ', '.join(ALLOWED_ENVIRONMENTS))
            raise RejectException('[POLICY] Alert environment does not match one of %s' %
                                  ', '.join(ALLOWED_ENVIRONMENTS))

        if not alert.service:
            LOG.warning('[POLICY] Alert must define a service')
            raise RejectException('[POLICY] Alert must define a service')

        return alert

    def post_receive(self, alert, **kwargs):
        return

    def status_change(self, alert, status, text, **kwargs):
        return

    def take_action(self, alert, action, text, **kwargs):
        raise NotImplementedError

    def delete(self, alert, **kwargs) -> bool:
        raise NotImplementedError
