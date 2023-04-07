## - Create new data source

### `URL`
```json
http://localhost:8081/api/datasource/create
```

### `request`

```json
{
    url: https://us-east-1-1.aws.cloud2.influxdata.com,
    token: Z0l0UrvG0xBdYN-zv4wBH6TCYn_g5nQ6GfoXnF67Av9Aj6Y,
    org: AI
    bucket: New backet
    name: New Datasource
    description: description
}
```

### `response`

```json
{
    "status": "success",
    "data": "{\"model\": \"base_app.modeldatasource\", \"pk\": 7, \"fields\": {\"url\": \"https://us-east-1-1.aws.cloud2.influxdata.com\", \"token\": \"Z0l0UrvG0xBdYN-zv4wBH6TCYn_g5nQ6GfoXnF67Av9Aj6YFh1cpo8mDLw2DfGeMsRbxpwhQXgqz_hnjvfhwMg==\", \"org\": \"org\", \"bucket\": \"data2\"}}"
}
```

## - Getting all data sources

### `URL`
```json
http://localhost:8081/api/datasource/create
```

### `request`

```json
{
    url: https://us-east-1-1.aws.cloud2.influxdata.com,
    token: Z0l0UrvG0xBdYN-zv4wBH6TCYn_g5nQ6GfoXnF67Av9Aj6Y,
    org: AI
    bucket: New backet
    name: New Datasource
    description: description
}
```

### `response`

```json
{
    "status": "success",
    "data": "{\"model\": \"base_app.modeldatasource\", \"pk\": 7, \"fields\": {\"url\": \"https://us-east-1-1.aws.cloud2.influxdata.com\", \"token\": \"Z0l0UrvG0xBdYN-zv4wBH6TCYn_g5nQ6GfoXnF67Av9Aj6YFh1cpo8mDLw2DfGeMsRbxpwhQXgqz_hnjvfhwMg==\", \"org\": \"org\", \"bucket\": \"data2\"}}"
}
```