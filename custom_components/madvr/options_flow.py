
# @staticmethod
# @callback
# def async_get_options_flow(config_entry: MadVRConfigEntry) -> OptionsFlow:
#     """Get the options flow for this handler."""
#     return MadVROptionsFlowHandler(config_entry)


# class MadVROptionsFlowHandler(OptionsFlow):
#     """Handle an options flow for the integration."""

#     def __init__(self, config_entry: MadVRConfigEntry) -> None:
#         """Initialize the options flow."""
#         self.config_entry = config_entry

#     async def async_step_init(
#         self, user_input: dict[str, Any] | None = None
#     ) -> ConfigFlowResult:
#         """Manage the options."""
#         return await self.async_step_user()

#     async def async_step_user(
#         self, user_input: dict[str, Any] | None = None
#     ) -> ConfigFlowResult:
#         """Handle the options step."""
#         errors: dict[str, str] = {}
#         if user_input is not None:
#             new_data = {**self.config_entry.data, **user_input}
#             # there could be a situation where user changes the IP to "add" a new device so we need to update mac too
#             try:
#                 # ensure we can connect and get the mac address from device
#                 mac = await test_connection(
#                     self.hass, user_input[CONF_HOST], user_input[CONF_PORT]
#                 )
#             except CannotConnect:
#                 _LOGGER.error("CannotConnect error caught")
#                 errors["base"] = "cannot_connect"
#             else:
#                 if not mac:
#                     errors["base"] = "no_mac"
#             if not errors:
#                 self.hass.config_entries.async_update_entry(
#                     self.config_entry, data=new_data
#                 )
#                 # reload the entity if changed
#                 await self.hass.config_entries.async_reload(self.config_entry.entry_id)
#                 return self.async_create_entry(title=DEFAULT_NAME, data=user_input)

#         # if error or initial load, show the form
#         options = self.config_entry.data
#         data_schema = vol.Schema(
#             {
#                 vol.Required(CONF_HOST, default=options.get(CONF_HOST, "")): str,
#                 vol.Required(CONF_PORT, default=options.get(CONF_PORT, 44077)): int,
#             }
#         )

#         return self.async_show_form(
#             step_id="user", data_schema=data_schema, errors=errors
#         )


# async def test_options_flow(
#     hass: HomeAssistant,
#     mock_madvr_client: AsyncMock,
#     mock_config_entry: MockConfigEntry,
# ) -> None:
#     """Test options flow."""
#     mock_config_entry.add_to_hass(hass)

#     result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

#     assert result["type"] == FlowResultType.FORM
#     assert result["step_id"] == "user"

#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input={
#             CONF_HOST: "192.168.1.100",
#             CONF_PORT: 44078,
#         },
#     )

#     assert result["type"] == FlowResultType.CREATE_ENTRY
#     assert result["data"] == {
#         CONF_HOST: "192.168.1.100",
#         CONF_PORT: 44078,
#     }
#     mock_madvr_client.open_connection.assert_called_once()
#     assert mock_madvr_client.async_add_tasks.call_count == 2
#     mock_madvr_client.async_cancel_tasks.assert_called_once()


# async def test_options_flow_errors(
#     hass: HomeAssistant,
#     mock_madvr_client: AsyncMock,
#     mock_config_entry: MockConfigEntry,
# ) -> None:
#     """Test options flow errors."""
#     mock_config_entry.add_to_hass(hass)

#     result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

#     assert result["type"] == FlowResultType.FORM
#     assert result["step_id"] == "user"

#     mock_madvr_client.open_connection.side_effect = TimeoutError

#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input={
#             CONF_HOST: "192.168.1.100",
#             CONF_PORT: 44078,
#         },
#     )

#     assert result["type"] == FlowResultType.FORM
#     assert result["errors"] == {"base": "cannot_connect"}

#     mock_madvr_client.open_connection.side_effect = None
#     mock_madvr_client.connected = True
#     mock_madvr_client.mac_address = None

#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input={
#             CONF_HOST: "192.168.1.100",
#             CONF_PORT: 44078,
#         },
#     )

#     assert result["type"] == FlowResultType.FORM
#     assert result["errors"] == {"base": "no_mac"}

#     mock_madvr_client.mac_address = MOCK_MAC

#     result = await hass.config_entries.options.async_configure(
#         result["flow_id"],
#         user_input={
#             CONF_HOST: "192.168.1.100",
#             CONF_PORT: 44078,
#         },
#     )

#     assert result["type"] == FlowResultType.CREATE_ENTRY
#     assert result["data"] == {
#         CONF_HOST: "192.168.1.100",
#         CONF_PORT: 44078,
#     }

# "options": {
#     "step": {
#       "user": {
#         "title": "Update madVR Envy settings",
#         "description": "Your device needs to be turned in order to update the integation settings. ",
#         "data": {
#           "host": "[%key:common::config_flow::data::host%]",
#           "port": "[%key:common::config_flow::data::port%]"
#         },
#         "data_description": {
#           "host": "The hostname or IP address of your madVR Envy device.",
#           "port": "The port your madVR Envy is listening on. In 99% of cases, leave this as the default."
#         }
#       }
#     },
#     "error": {
#       "cannot_connect": "[%key:common::config_flow::error::cannot_connect%]",
#       "no_mac": "A MAC address was not found. It required to identify the device. Please ensure your device is connectable."
#     }
#   },