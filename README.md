## How to run?

1. Run the ex_app

   ```bash
   NC_HOST="localhost" \
   NC_SUBFOLDER_PATH="" \
   docker compose up
   ```

   > use `NC_SUBFOLDER_PATH` env if Nextcloud is running in a subfolder.
   > e.g. `NC_SUBFOLDER_PATH="nextcloud"`

2. Register ex_app in Nextcloud

   ```bash
   sudo -u www-data php occ app_api:app:register openproject manual_install --json-info \
   '{"id":"openproject","name":"Openproject Exapp","daemon_config_name":"manual_install","version":"1.0.0","secret":"12345","scopes":["ALL"],"port":9030,"system":0}' \
   --force-scopes --wait-finish
   ```

3. Access OpenProject

   URL: http://{NC_HOST}/{NC_SUBFOLDER_PATH}/index.php/apps/app_api/proxy/openproject
