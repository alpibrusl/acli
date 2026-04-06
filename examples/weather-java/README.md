# weather (Java)

Java port of [`../weather/weather.py`](../weather/weather.py): same simulated cities, commands, JSON envelopes, NDJSON `refresh`, and dry-run exit code `9` for `favorite --dry-run`.

## Build

Install the Java SDK, then build this module:

```bash
mvn install -f ../../sdks/java/pom.xml -DskipTests
cd examples/weather-java && mvn test
```

## Run

```bash
mvn -q exec:java -Dexec.args="get --city london --output json"
mvn -q exec:java -Dexec.args="introspect --output json"
```

After `mvn package`, run with `java -cp ...` including `target/classes`, `../../sdks/java/target/acli-spec-0.3.0.jar`, and Picocli/Jackson from Maven dependencies, or use `exec:java` as above.

## License

[EUPL-1.2](../../LICENSE)
