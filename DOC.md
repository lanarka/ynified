# ynified

```	
	!source      <path-to-file> Extend node with source (yaml/json)
	!source-bson <path-to-file> Extend node with source (bson)
	
	!load-text   <path-to-file> Extend node with text from file
	!load-binary <path-to-file> Extend node with binary data from file
	!load-base64 <path-to-file> Extend node with binary data from file (Base64 encoded)
	
	!eval        <python-expression> Extend node with python expression
	!query       <query-expression> Extend node with specific query expression
```

## Tools

### !now

```yaml
now: !now
```

```json
{
	"now": 23296549656,
}
```


### !now-fmt

```yaml
now: !now-fmt %H:%M:%S
```

```json
{
	"now": "12:34:56",
}
```
