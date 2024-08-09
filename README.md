## Run the Setup

1. Start OpenProject

   ```bash
   NC_SUBFOLDER_PATH="" docker compose up
   ```

   > use `NC_SUBFOLDER_PATH` env if Nextcloud is running in a subfolder.

2. Start ex_app

   ```bash
   NC_SUBFOLDER_PATH="" bash exapp.sh
   ```

3. Register ex_app in Nextcloud

   ```bash
   sudo -u www-data php occ app_api:app:register openproject manual_install --json-info \
   '{"id":"openproject","name":"Openproject Exapp","daemon_config_name":"manual_install","version":"1.0.0","secret":"12345","scopes":["ALL"],"port":9030,"system":0}' \
   --force-scopes --wait-finish
   ```

4. Access OpenProject

   URL: http://localhost/{NC_SUBFOLDER_PATH}/index.php/apps/app_api/proxy/openproject
