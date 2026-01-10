#!/usr/bin/env python3
"""
CrossPacket - Cross-Platform Packet Generator

A cross-platform data packet generator for multi-language projects.
Generates type-safe packet classes from a single JSON definition.

Supported Targets:
- Dart/Flutter (2-space indent)
- Python (4-space indent, PEP 8)
- Java (4-space indent)
- TypeScript/Node.js (2-space indent)
- Rust (4-space indent)
- Go (tabs)
- C++ (4-space indent)
- PHP (4-space indent, PSR-12)

Serialization Formats:
- JSON for debugging and interoperability
- MessagePack for performance and binary efficiency

Usage:
  python generate.py [options]

  Options:
    --config FILE       Path to packets.json config file
    --dart              Generate Dart code
    --python            Generate Python code
    --java              Generate Java code
    --typescript        Generate TypeScript code
    --rust              Generate Rust code
    --go                Generate Go code
    --cpp               Generate C++ code
    --php               Generate PHP code
    --all               Generate all platforms
    --override          Override existing files
    --clean             Remove old generated files before generating

Author: Serhat Güler (sero583)
GitHub: https://github.com/sero583
License: MIT
Version: 1.0.0
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

__version__ = "1.0.0"
__author__ = "Serhat Güler (sero583)"
__author_github__ = "https://github.com/sero583"
__license__ = "MIT"

# Type mappings for each language
TYPE_MAPPINGS = {
    "int": {
        "dart": "int",
        "python": "int",
        "java": "long",
        "typescript": "number",
        "rust": "i64",
        "go": "int64",
        "cpp": "int64_t",
        "csharp": "long",
        "php": "int",
    },
    "float": {
        "dart": "double",
        "python": "float",
        "java": "double",
        "typescript": "number",
        "rust": "f64",
        "go": "float64",
        "cpp": "double",
        "csharp": "double",
        "php": "float",
    },
    "double": {
        "dart": "double",
        "python": "float",
        "java": "double",
        "typescript": "number",
        "rust": "f64",
        "go": "float64",
        "cpp": "double",
        "csharp": "double",
        "php": "float",
    },
    "bool": {
        "dart": "bool",
        "python": "bool",
        "java": "boolean",
        "typescript": "boolean",
        "rust": "bool",
        "go": "bool",
        "cpp": "bool",
        "csharp": "bool",
        "php": "bool",
    },
    "string": {
        "dart": "String",
        "python": "str",
        "java": "String",
        "typescript": "string",
        "rust": "String",
        "go": "string",
        "cpp": "std::string",
        "csharp": "string",
        "php": "string",
    },
    "datetime": {
        "dart": "DateTime",
        "python": "datetime",
        "java": "ZonedDateTime",
        "typescript": "Date",
        "rust": "DateTime<Utc>",
        "go": "time.Time",
        "cpp": "std::string",
        "csharp": "DateTimeOffset",
        "php": "DateTimeImmutable",
    },
    "time": {
        "dart": "TimeOfDay",
        "python": "time",
        "java": "LocalTime",
        "typescript": "string",
        "rust": "NaiveTime",
        "go": "string",
        "cpp": "std::string",
        "csharp": "TimeSpan",
        "php": "string",
    },
    "bytes": {
        "dart": "Uint8List",
        "python": "bytes",
        "java": "byte[]",
        "typescript": "Uint8Array",
        "rust": "Vec<u8>",
        "go": "[]byte",
        "cpp": "std::vector<uint8_t>",
        "csharp": "byte[]",
        "php": "string",
    },
    "list": {
        "dart": "List<dynamic>",
        "python": "List[Any]",
        "java": "List<Object>",
        "typescript": "any[]",
        "rust": "Vec<serde_json::Value>",
        "go": "[]interface{}",
        "cpp": "std::string",
        "csharp": "List<object>",
        "php": "array",
    },
    "list_int": {
        "dart": "List<int>",
        "python": "List[int]",
        "java": "List<Long>",
        "typescript": "number[]",
        "rust": "Vec<i64>",
        "go": "[]int64",
        "cpp": "std::vector<int64_t>",
        "csharp": "List<long>",
        "php": "array",
    },
    "list_string": {
        "dart": "List<String>",
        "python": "List[str]",
        "java": "List<String>",
        "typescript": "string[]",
        "rust": "Vec<String>",
        "go": "[]string",
        "cpp": "std::vector<std::string>",
        "csharp": "List<string>",
        "php": "array",
    },
    "map": {
        "dart": "Map<String, dynamic>",
        "python": "Dict[str, Any]",
        "java": "Map<String, Object>",
        "typescript": "Record<string, any>",
        "rust": "HashMap<String, serde_json::Value>",
        "go": "map[string]interface{}",
        "cpp": "std::string",
        "csharp": "Dictionary<string, object>",
        "php": "array",
    },
    "embedded_map": {
        "dart": "Map<dynamic, dynamic>",
        "python": "Dict[Any, Any]",
        "java": "Map<Object, Object>",
        "typescript": "Map<any, any>",
        "rust": "HashMap<String, serde_json::Value>",
        "go": "map[string]interface{}",
        "cpp": "std::string",
        "csharp": "Dictionary<string, object>",  # Keys stringified for JSON compatibility
        "php": "array",
    },
    "map_string_dynamic": {
        "dart": "Map<String, dynamic>",
        "python": "Dict[str, Any]",
        "java": "Map<String, Object>",
        "typescript": "Record<string, any>",
        "rust": "HashMap<String, serde_json::Value>",
        "go": "map[string]interface{}",
        "cpp": "std::string",
        "csharp": "Dictionary<string, object>",
        "php": "array",
    },
}


def to_pascal_case(text: str) -> str:
    """Convert text to PascalCase."""
    # If already PascalCase, return as-is
    if text and text[0].isupper() and "_" not in text:
        return text
    # Convert snake_case to PascalCase
    return "".join(word.capitalize() for word in text.split("_"))


def to_snake_case(text: str) -> str:
    """Convert text to snake_case."""
    # Insert underscore before uppercase letters and convert to lowercase
    result = re.sub(r"(?<!^)(?=[A-Z])", "_", text).lower()
    return result


def to_camel_case(text: str) -> str:
    """Convert text to camelCase."""
    parts = text.split("_")
    return parts[0].lower() + "".join(word.capitalize() for word in parts[1:])


class PacketField:
    """Represents a packet field with type and metadata."""
    
    def __init__(self, name: str, field_def: Any):
        self.name = name
        if isinstance(field_def, str):
            self.type = field_def
            self.description = None
            self.optional = False
            self.deprecated = False
            self.validation = {}
        else:
            self.type = field_def.get("type", "string")
            self.description = field_def.get("description")
            self.optional = field_def.get("optional", False)
            self.deprecated = field_def.get("deprecated", False)
            self.validation = field_def.get("validation", {})
    
    @property
    def required(self) -> bool:
        """Check if field is required (default True unless optional or validation.required=False)."""
        if self.optional:
            return False
        return self.validation.get("required", True)
    
    @property
    def min_value(self) -> Optional[float]:
        """Get minimum value/length from validation."""
        return self.validation.get("min")
    
    @property
    def max_value(self) -> Optional[float]:
        """Get maximum value/length from validation."""
        return self.validation.get("max")
    
    @property
    def pattern(self) -> Optional[str]:
        """Get regex pattern for string validation."""
        return self.validation.get("pattern")
    
    @property
    def allow_empty(self) -> bool:
        """Check if empty values are allowed."""
        return self.validation.get("allow_empty", True)
    
    @property
    def allow_nan(self) -> bool:
        """Check if NaN is allowed for float fields."""
        return self.validation.get("allow_nan", False)
    
    @property
    def allow_infinity(self) -> bool:
        """Check if Infinity is allowed for float fields."""
        return self.validation.get("allow_infinity", False)
    
    @property
    def max_depth(self) -> int:
        """Get maximum nesting depth for list/map fields."""
        return self.validation.get("max_depth", 10)
    
    def dart_type(self) -> str:
        """Get Dart type for this field."""
        base_type = TYPE_MAPPINGS.get(self.type, {}).get("dart", "dynamic")
        return f"{base_type}?" if self.optional else base_type
    
    def cpp_type(self) -> str:
        """Get C++ type for this field."""
        return TYPE_MAPPINGS.get(self.type, {}).get("cpp", "std::string")
    
    def php_type(self) -> str:
        """Get PHP type for this field."""
        return TYPE_MAPPINGS.get(self.type, {}).get("php", "mixed")


class PacketDefinition:
    """Represents a packet definition."""
    
    def __init__(self, path: str, definition: Dict[str, Any]):
        self.path = path
        self.name = to_pascal_case(path.split("/")[-1])
        self.description = definition.get("description", "")
        self.version = definition.get("version", 1)
        self.deprecated = definition.get("deprecated", False)
        self.fields: List[PacketField] = []
        
        fields_def = definition.get("fields", {})
        for field_name, field_def in fields_def.items():
            self.fields.append(PacketField(field_name, field_def))
    
    def has_datetime(self) -> bool:
        """Check if packet has datetime fields."""
        return any(f.type == "datetime" for f in self.fields)
    
    def has_time(self) -> bool:
        """Check if packet has time fields."""
        return any(f.type == "time" for f in self.fields)
    
    def has_embedded_map(self) -> bool:
        """Check if packet has embedded_map fields."""
        return any(f.type == "embedded_map" for f in self.fields)
    
    def has_bytes(self) -> bool:
        """Check if packet has bytes fields."""
        return any(f.type == "bytes" for f in self.fields)
    
    def has_list(self) -> bool:
        """Check if packet has list fields."""
        return any(f.type in ["list", "list_int", "list_string"] for f in self.fields)
    
    def has_map(self) -> bool:
        """Check if packet has map fields."""
        return any(f.type in ["map", "embedded_map", "map_string_dynamic"] for f in self.fields)


class DartGenerator:
    """Generates Dart/Flutter packet code."""
    
    def __init__(self, config: Dict[str, Any]):
        self.output_dir = Path(config.get("output_dir", "./generated/dart"))
        self.base_package = config.get("base_package", "data_packets")
        self.indent = config.get("indent", "  ")  # Dart uses 2 spaces
        self.no_msgpack = False
        self.no_json = False
    
    def _i(self, level: int = 1) -> str:
        """Return indentation for the given level."""
        return self.indent * level
    
    def dart_encode(self, field: PacketField) -> str:
        """Generate Dart encode expression for a field.
        
        All fields are nullable to support empty constructor pattern.
        """
        name = field.name
        if field.type == "datetime":
            return f"{name} != null ? _formatDateTimeWithTimezone({name}!) : null"
        elif field.type == "time":
            return f"{name} != null ? '${{{name}!.hour.toString().padLeft(2, '0')}}:${{{name}!.minute.toString().padLeft(2, '0')}}' : null"
        elif field.type in ["int", "float", "double", "bool", "string"]:
            return name
        elif field.type in ["list", "list_int", "list_string", "map", "embedded_map", "map_string_dynamic"]:
            return name
        elif field.type == "bytes":
            return f"{name} != null ? base64Encode({name}!) : null"
        else:
            return f"{name}?.toJson()"
    
    def dart_decode(self, field: PacketField) -> str:
        """Generate Dart decode expression for a field.
        
        All fields are nullable to support empty constructor pattern.
        """
        name = field.name
        if field.type == "datetime":
            return f"json['{name}'] != null ? DateTime.parse(json['{name}']) : null"
        elif field.type == "time":
            return f"json['{name}'] != null ? TimeOfDay(hour: int.parse(json['{name}'].split(':')[0]), minute: int.parse(json['{name}'].split(':')[1])) : null"
        elif field.type in ["int", "bool", "string"]:
            return f"json['{name}']"
        elif field.type in ["float", "double"]:
            return f"(json['{name}'] as num?)?.toDouble()"
        elif field.type == "list":
            return f"json['{name}'] as List<dynamic>?"
        elif field.type == "list_int":
            return f"(json['{name}'] as List<dynamic>?)?.map((e) => e as int).toList()"
        elif field.type == "list_string":
            return f"(json['{name}'] as List<dynamic>?)?.map((e) => e.toString()).toList()"
        elif field.type == "embedded_map":
            return f"json['{name}'] != null ? _deepConvertMap(json['{name}']) : null"
        elif field.type in ["map", "map_string_dynamic"]:
            return f"json['{name}'] != null ? Map<String, dynamic>.from(json['{name}'] as Map) : null"
        elif field.type == "bytes":
            return f"json['{name}'] != null ? base64Decode(json['{name}']) : null"
        else:
            return f"json['{name}']"
    
    def generate_packet(self, packet: PacketDefinition) -> str:
        """Generate Dart code for a packet."""
        lines = []
        
        # File header
        lines.append("// This file is auto-generated. Do not modify manually.")
        lines.append("// Generated by CrossPacket")
        
        # Conditional imports based on serialization mode
        # dart:convert is needed for JSON or for bytes (base64) in serialize()
        if not self.no_json or packet.has_bytes():
            lines.append("import 'dart:convert';")
        # dart:typed_data is needed for MsgPack or for bytes fields
        if not self.no_msgpack or packet.has_bytes():
            lines.append("import 'dart:typed_data';")
        if not self.no_msgpack:
            lines.append("import 'package:msgpack_dart/msgpack_dart.dart' as msgpack;")
        
        # data_packet.dart exports TimeOfDay class (pure Dart, no Flutter dependency)
        lines.append("import '../data_packet.dart';")
        
        lines.append("")
        
        # DateTime helper if needed
        if packet.has_datetime():
            lines.extend(self._generate_datetime_helper())
        
        # Deep map conversion helper if needed (for embedded_map fields in JSON and MsgPack)
        if packet.has_embedded_map():
            lines.extend(self._generate_deep_convert_helper())
        
        # Class documentation
        if packet.description:
            lines.append(f"/// {packet.description}")
        
        # Class definition
        lines.append(f"class {packet.name} extends DataPacket {{")
        
        # Fields - all nullable to support empty constructor + setters pattern
        for field in packet.fields:
            if field.description:
                lines.append(f"{self._i()}/// {field.description}")
            # All fields are nullable and non-final to support setters
            dart_type = field.dart_type()
            if not dart_type.endswith('?'):
                dart_type = f"{dart_type}?"
            lines.append(f"{self._i()}{dart_type} {field.name};")
        
        lines.append("")
        
        # Default empty constructor
        lines.append(f"{self._i()}/// Creates an empty [{packet.name}]. Use setters to populate fields.")
        lines.append(f"{self._i()}{packet.name}();")
        lines.append("")
        
        # Named constructor for parameterized initialization
        if packet.fields:
            lines.append(f"{self._i()}/// Creates a [{packet.name}] with all fields.")
            lines.append(f"{self._i()}{packet.name}.create({{")
            for field in packet.fields:
                lines.append(f"{self._i(2)}this.{field.name},")
            lines.append(f"{self._i()}}});")
        
        lines.append("")
        
        # Type getter
        lines.append(f"{self._i()}@override")
        lines.append(f"{self._i()}String get type => '{packet.path}';")
        lines.append("")
        
        # serialize method (always needed)
        lines.append(f"{self._i()}@override")
        lines.append(f"{self._i()}Map<String, dynamic> serialize() => {{")
        lines.append(f"{self._i(2)}'{self.type_field}': type,")
        for field in packet.fields:
            lines.append(f"{self._i(2)}'{field.name}': {self.dart_encode(field)},")
        lines.append(f"{self._i()}}};")
        lines.append("")
        
        # _fromMap private helper (used by fromJson and fromMsgPack)
        lines.append(f"{self._i()}/// Creates a [{packet.name}] from a JSON map (internal helper).")
        lines.append(f"{self._i()}static {packet.name} _fromMap(Map<String, dynamic> json) =>")
        if packet.fields:
            lines.append(f"{self._i(2)}{packet.name}.create(")
            for field in packet.fields:
                lines.append(f"{self._i(3)}{field.name}: {self.dart_decode(field)},")
            lines.append(f"{self._i(2)});")
        else:
            lines.append(f"{self._i(2)}{packet.name}();")
        lines.append("")
        
        # toJson method (only if JSON enabled)
        if not self.no_json:
            lines.append(f"{self._i()}/// Serializes this packet to a JSON string.")
            lines.append(f"{self._i()}String toJson() => jsonEncode(serialize());")
            lines.append("")
            
            lines.append(f"{self._i()}/// Creates a [{packet.name}] from a JSON string.")
            lines.append(f"{self._i()}static {packet.name} fromJson(String jsonString) {{")
            lines.append(f"{self._i(2)}return _fromMap(jsonDecode(jsonString) as Map<String, dynamic>);")
            lines.append(f"{self._i()}}}")
            lines.append("")
        
        # toMsgPack method (only if MsgPack enabled)
        if not self.no_msgpack:
            lines.append(f"{self._i()}/// Serializes this packet to MessagePack binary format.")
            lines.append(f"{self._i()}Uint8List toMsgPack() => msgpack.serialize(serialize());")
            lines.append("")
            
            # fromMsgPack factory
            lines.append(f"{self._i()}/// Creates a [{packet.name}] from MessagePack binary data.")
            lines.append(f"{self._i()}static {packet.name} fromMsgPack(Uint8List bytes) {{")
            lines.append(f"{self._i(2)}final data = msgpack.deserialize(bytes);")
            lines.append(f"{self._i(2)}return _fromMap(Map<String, dynamic>.from(data as Map));")
            lines.append(f"{self._i()}}}")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _generate_datetime_helper(self) -> List[str]:
        """Generate DateTime timezone helper function."""
        return [
            "/// Formats a DateTime with timezone offset (ISO 8601).",
            "String _formatDateTimeWithTimezone(DateTime dt) {",
            f"{self._i()}final offset = dt.timeZoneOffset;",
            f"{self._i()}final offsetSign = offset.isNegative ? '-' : '+';",
            f"{self._i()}final offsetHours = offset.abs().inHours.toString().padLeft(2, '0');",
            f"{self._i()}final offsetMinutes = (offset.abs().inMinutes % 60).toString().padLeft(2, '0');",
            f"{self._i()}final year = dt.year.toString().padLeft(4, '0');",
            f"{self._i()}final month = dt.month.toString().padLeft(2, '0');",
            f"{self._i()}final day = dt.day.toString().padLeft(2, '0');",
            f"{self._i()}final hour = dt.hour.toString().padLeft(2, '0');",
            f"{self._i()}final minute = dt.minute.toString().padLeft(2, '0');",
            f"{self._i()}final second = dt.second.toString().padLeft(2, '0');",
            f"{self._i()}final millisecond = dt.millisecond.toString().padLeft(3, '0');",
            f"{self._i()}return '$year-$month-${{day}}T$hour:$minute:$second.$millisecond$offsetSign$offsetHours:$offsetMinutes';",
            "}",
            "",
        ]
    
    def _generate_deep_convert_helper(self) -> List[str]:
        """Generate deep map conversion helpers for msgpack compatibility."""
        return [
            "/// Safely converts nested msgpack maps to Map<String, dynamic>.",
            "Map<String, dynamic> _deepConvertMap(dynamic value) {",
            f"{self._i()}if (value == null) return {{}};",
            f"{self._i()}if (value is! Map) return {{}};",
            f"{self._i()}return _safeMapConvert(value);",
            "}",
            "",
            "/// Recursively converts List elements.",
            "List<dynamic> _safeListConvert(List<dynamic> list) {",
            f"{self._i()}return list.map((item) {{",
            f"{self._i(2)}if (item is Map) return _safeMapConvert(item);",
            f"{self._i(2)}if (item is List) return _safeListConvert(item);",
            f"{self._i(2)}return item;",
            f"{self._i()}}}).toList();",
            "}",
            "",
            "/// Recursively converts Map<dynamic, dynamic> to Map<String, dynamic>.",
            "Map<String, dynamic> _safeMapConvert(Map<dynamic, dynamic> map) {",
            f"{self._i()}return map.map((key, value) {{",
            f"{self._i(2)}final stringKey = key?.toString() ?? '';",
            f"{self._i(2)}dynamic convertedValue;",
            f"{self._i(2)}if (value is Map) {{",
            f"{self._i(3)}convertedValue = _safeMapConvert(value);",
            f"{self._i(2)}}} else if (value is List) {{",
            f"{self._i(3)}convertedValue = _safeListConvert(value);",
            f"{self._i(2)}}} else {{",
            f"{self._i(3)}convertedValue = value;",
            f"{self._i(2)}}}",
            f"{self._i(2)}return MapEntry(stringKey, convertedValue);",
            f"{self._i()}}});",
            "}",
            "",
        ]
    
    def _generate_time_of_day_class(self) -> List[str]:
        """Generate a pure Dart TimeOfDay class (no Flutter dependency)."""
        return [
            "/// A pure Dart TimeOfDay class (no Flutter dependency).",
            "/// Represents a time of day with hour and minute components.",
            "class TimeOfDay {",
            f"{self._i()}/// The hour of the day, from 0 to 23.",
            f"{self._i()}final int hour;",
            f"{self._i()}/// The minute of the hour, from 0 to 59.",
            f"{self._i()}final int minute;",
            "",
            f"{self._i()}/// Creates a TimeOfDay with the given hour and minute.",
            f"{self._i()}const TimeOfDay({{required this.hour, required this.minute}});",
            "",
            f"{self._i()}/// Formats the time as HH:mm.",
            f"{self._i()}String format() {{",
            f"{self._i(2)}final h = hour.toString().padLeft(2, '0');",
            f"{self._i(2)}final m = minute.toString().padLeft(2, '0');",
            f"{self._i(2)}return '$h:$m';",
            f"{self._i()}}}",
            "",
            f"{self._i()}@override",
            f"{self._i()}String toString() => 'TimeOfDay(hour: $hour, minute: $minute)';",
            "",
            f"{self._i()}@override",
            f"{self._i()}bool operator ==(Object other) {{",
            f"{self._i(2)}return other is TimeOfDay && other.hour == hour && other.minute == minute;",
            f"{self._i()}}}",
            "",
            f"{self._i()}@override",
            f"{self._i()}int get hashCode => hour.hashCode ^ minute.hashCode;",
            "}",
        ]
    
    def generate_base_class(self, packets: List[PacketDefinition]) -> str:
        """Generate the base DataPacket class.
        
        Respects no_msgpack and no_json flags to only include available methods.
        """
        lines = [
            "// This file is auto-generated. Do not modify manually.",
            "// Generated by CrossPacket",
        ]
        
        # Only include necessary imports based on mode
        if not self.no_json:
            lines.append("import 'dart:convert';")
        lines.append("import 'dart:typed_data';")
        if not self.no_msgpack:
            lines.append("import 'package:msgpack_dart/msgpack_dart.dart' as msgpack;")
        
        # Import all generated packets FIRST (before any class declarations)
        for packet in packets:
            filename = to_snake_case(packet.name)
            lines.append(f"import './generated/{filename}.dart';")
        
        lines.append("")
        
        # Check if any packet has a time field - if so, include TimeOfDay class
        has_time_field = any(packet.has_time() for packet in packets)
        if has_time_field:
            lines.extend(self._generate_time_of_day_class())
            lines.append("")
        
        lines.extend([
            "/// Base class for all data packets.",
            "abstract class DataPacket {",
            f"{self._i()}/// The packet type identifier.",
            f"{self._i()}String get type;",
            "",
            f"{self._i()}/// Serializes the packet to a Map.",
            f"{self._i()}Map<String, dynamic> serialize();",
        ])
        
        # JSON methods (only if JSON is enabled)
        if not self.no_json:
            lines.extend([
                "",
                f"{self._i()}/// Converts the packet to a JSON string.",
                f"{self._i()}String toJson() => jsonEncode(serialize());",
                "",
                f"{self._i()}/// Creates a DataPacket from a JSON string.",
                f"{self._i()}static DataPacket fromJson(String jsonString) {{",
                f"{self._i(2)}return deserialize(jsonDecode(jsonString) as Map<String, dynamic>);",
                f"{self._i()}}}",
            ])
        
        # MsgPack methods (only if MsgPack is enabled)
        if not self.no_msgpack:
            lines.extend([
                "",
                f"{self._i()}/// Serializes the packet to MessagePack binary format.",
                f"{self._i()}Uint8List toMsgPack() => msgpack.serialize(serialize());",
                "",
                f"{self._i()}/// Creates a DataPacket from MessagePack binary data.",
                f"{self._i()}static DataPacket fromMsgPack(Uint8List bytes) {{",
                f"{self._i(2)}final data = msgpack.deserialize(bytes);",
                f"{self._i(2)}return deserialize(Map<String, dynamic>.from(data as Map));",
                f"{self._i()}}}",
            ])
        
        # Deserialize method - use appropriate deserialization based on mode
        lines.extend([
            "",
            f"{self._i()}/// Creates a DataPacket from a deserialized Map.",
            f"{self._i()}static DataPacket deserialize(Map<String, dynamic> data) {{",
            f"{self._i(2)}switch (data['{self.type_field}']) {{",
        ])
        
        # Switch cases for each packet type
        # Use fromJson if available, otherwise fromMsgPack
        for packet in packets:
            lines.append(f"{self._i(3)}case '{packet.path}':")
            if not self.no_json:
                lines.append(f"{self._i(4)}return {packet.name}.fromJson(jsonEncode(data));")
            else:
                # In MsgPack-only mode, we use fromMsgPack with a serialized map
                lines.append(f"{self._i(4)}return {packet.name}.fromMsgPack(msgpack.serialize(data));")
        
        lines.extend([
            f"{self._i(3)}default:",
            f"{self._i(4)}throw UnimplementedError('Unknown packet type: ${{data[\'{self.type_field}\']}}');",
            f"{self._i(2)}}}",
            f"{self._i()}}}",
            "}",
        ])
        
        return "\n".join(lines)
    
    def generate(self, packets: List[PacketDefinition], override: bool = False, clean: bool = False, no_msgpack: bool = False, no_json: bool = False, type_field: str = "packetType"):
        """Generate all Dart files."""
        self.type_field = type_field
        self.no_msgpack = no_msgpack
        self.no_json = no_json
        generated_dir = self.output_dir / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        
        if clean:
            for file in generated_dir.glob("*.dart"):
                file.unlink()
        
        # Generate base class
        base_path = self.output_dir / "data_packet.dart"
        if not base_path.exists() or override:
            base_path.write_text(self.generate_base_class(packets))
            print(f"Generated: {base_path}")
        
        # Generate individual packets
        for packet in packets:
            filename = to_snake_case(packet.name) + ".dart"
            filepath = generated_dir / filename
            if not filepath.exists() or override:
                filepath.write_text(self.generate_packet(packet))
                print(f"Generated: {filepath}")
            else:
                print(f"Skipped (exists): {filepath}")


class PythonGenerator:
    """Generates Python packet code with full serialization support."""
    
    def __init__(self, config: Dict[str, Any]):
        self.output_dir = Path(config.get("output_dir", "./generated/python"))
        self.indent = config.get("indent", "    ")  # PEP 8: 4 spaces
    
    def _i(self, level: int = 1) -> str:
        """Return indentation for the given level."""
        return self.indent * level
    
    def python_type(self, field: PacketField) -> str:
        """Get Python type annotation for a field.
        
        All fields are Optional to support empty constructor + setters pattern.
        """
        base_type = TYPE_MAPPINGS.get(field.type, {}).get("python", "Any")
        # All fields are Optional to allow empty constructor
        return f"Optional[{base_type}]"
    
    def python_encode(self, field: PacketField) -> str:
        """Generate Python encode expression for a field.
        
        All fields can be None (supports empty constructor pattern).
        """
        name = f"self.{field.name}"
        if field.type == "datetime":
            return f"{name}.isoformat() if {name} else None"
        elif field.type == "time":
            return f"{name}.isoformat() if {name} else None"
        else:
            return name
    
    def python_decode(self, field: PacketField, source: str = "data") -> str:
        """Generate Python decode expression for a field.
        
        All fields can be None (supports empty constructor pattern).
        """
        getter = f"{source}.get('{field.name}')"
        if field.type == "datetime":
            return f"datetime.fromisoformat({getter}) if {getter} else None"
        elif field.type == "time":
            return f"time.fromisoformat({getter}) if {getter} else None"
        elif field.type == "list":
            return f"{getter}"
        elif field.type == "list_int":
            return f"[int(x) for x in {getter}] if {getter} else None"
        elif field.type == "list_string":
            return f"[str(x) for x in {getter}] if {getter} else None"
        elif field.type in ["map", "embedded_map", "map_string_dynamic"]:
            return f"{getter}"
        elif field.type == "int":
            return f"int({getter}) if {getter} is not None else None"
        elif field.type in ["float", "double"]:
            return f"float({getter}) if {getter} is not None else None"
        elif field.type == "bool":
            return f"bool({getter}) if {getter} is not None else None"
        else:
            return getter
    
    def generate_packet(self, packet: PacketDefinition) -> str:
        """Generate Python code for a packet."""
        lines = []
        
        # File header
        lines.append('"""')
        lines.append(f"Auto-generated packet: {packet.name}")
        if packet.description:
            lines.append(f"{packet.description}")
        lines.append('"""')
        lines.append("from __future__ import annotations")
        lines.append("")
        
        # Conditional imports based on serialization mode
        if not self.no_json:
            lines.append("import json")
        lines.append("from dataclasses import dataclass, field")
        lines.append("from typing import Any, ClassVar, Dict, List, Optional")
        
        # Conditional imports
        if packet.has_datetime() or packet.has_time():
            lines.append("from datetime import datetime, timezone")
        if packet.has_time():
            lines.append("from datetime import time")
        
        # MsgPack import only if not no_msgpack
        if not self.no_msgpack:
            lines.append("")
            lines.append("try:")
            lines.append(f"{self._i()}import msgpack")
            lines.append(f"{self._i()}HAS_MSGPACK = True")
            lines.append("except ImportError:")
            lines.append(f"{self._i()}HAS_MSGPACK = False")
        lines.append("")
        
        # Dataclass definition
        lines.append("@dataclass")
        lines.append(f"class {packet.name}:")
        
        # Docstring
        if packet.description:
            lines.append(f'{self._i()}"""{packet.description}"""')
        else:
            lines.append(f'{self._i()}"""Data packet for {packet.path}."""')
        lines.append("")
        
        # Class constant (ClassVar is not part of __init__)
        lines.append(f'{self._i()}TYPE: ClassVar[str] = "{packet.path}"')
        lines.append("")
        
        # All fields have None defaults to support empty constructor + setters pattern
        for field in packet.fields:
            type_hint = self.python_type(field)
            lines.append(f"{self._i()}{field.name}: {type_hint} = None")
        
        lines.append("")
        
        # _to_dict method (private - internal helper for serialization)
        lines.append(f"{self._i()}def _to_dict(self) -> Dict[str, Any]:")
        lines.append(f'{self._i(2)}"""Convert to dictionary for serialization (internal)."""')
        lines.append(f"{self._i(2)}return {{")
        lines.append(f'{self._i(3)}"{self.type_field}": self.TYPE,')
        for field in packet.fields:
            lines.append(f'{self._i(3)}"{field.name}": {self.python_encode(field)},')
        lines.append(f"{self._i(2)}}}")
        lines.append("")
        
        # to_json method (only if JSON enabled)
        if not self.no_json:
            lines.append(f"{self._i()}def to_json(self) -> str:")
            lines.append(f'{self._i(2)}"""Serialize to JSON string."""')
            lines.append(f"{self._i(2)}return json.dumps(self._to_dict(), default=str)")
            lines.append("")
        
        # to_msgpack method (only if MsgPack enabled)
        if not self.no_msgpack:
            lines.append(f"{self._i()}def to_msgpack(self) -> bytes:")
            lines.append(f'{self._i(2)}"""Serialize to MessagePack binary format."""')
            lines.append(f"{self._i(2)}if not HAS_MSGPACK:")
            lines.append(f'{self._i(3)}raise ImportError("msgpack is required for binary serialization")')
            lines.append(f"{self._i(2)}return msgpack.packb(self._to_dict(), use_bin_type=True)")
            lines.append("")
        
        # _from_dict class method (private - internal helper)
        lines.append(f"{self._i()}@classmethod")
        lines.append(f"{self._i()}def _from_dict(cls, data: Dict[str, Any]) -> {packet.name}:")
        lines.append(f'{self._i(2)}"""Create instance from dictionary (internal)."""')
        lines.append(f"{self._i(2)}return cls(")
        for field in packet.fields:
            lines.append(f"{self._i(3)}{field.name}={self.python_decode(field)},")
        lines.append(f"{self._i(2)})")
        lines.append("")
        
        # from_json class method (only if JSON enabled)
        if not self.no_json:
            lines.append(f"{self._i()}@classmethod")
            lines.append(f"{self._i()}def from_json(cls, json_str: str) -> {packet.name}:")
            lines.append(f'{self._i(2)}"""Deserialize from JSON string."""')
            lines.append(f"{self._i(2)}return cls._from_dict(json.loads(json_str))")
            lines.append("")
        
        # from_msgpack class method (only if MsgPack enabled)
        if not self.no_msgpack:
            lines.append(f"{self._i()}@classmethod")
            lines.append(f"{self._i()}def from_msgpack(cls, data: bytes) -> {packet.name}:")
            lines.append(f'{self._i(2)}"""Deserialize from MessagePack binary format."""')
            lines.append(f"{self._i(2)}if not HAS_MSGPACK:")
            lines.append(f'{self._i(3)}raise ImportError("msgpack is required for binary deserialization")')
            lines.append(f"{self._i(2)}return cls._from_dict(msgpack.unpackb(data, raw=False))")
        
        return "\n".join(lines)
    
    def generate_init(self, packets: List[PacketDefinition]) -> str:
        """Generate __init__.py with imports and deserialize function."""
        lines = [
            '"""',
            "Auto-generated packet module.",
            '"""',
            "",
        ]
        
        # Import all packets
        for packet in packets:
            filename = to_snake_case(packet.name)
            lines.append(f"from .{filename} import {packet.name}")
        
        lines.append("")
        lines.append("")
        
        # Deserialize function
        lines.append("def deserialize_packet(data):")
        lines.append(f'{self._i()}"""Deserialize a packet based on its {self.type_field} field."""')
        lines.append(f'{self._i()}packet_type = data.get("{self.type_field}") if isinstance(data, dict) else None')
        lines.append("")
        
        for packet in packets:
            lines.append(f'{self._i()}if packet_type == "{packet.path}":')
            lines.append(f"{self._i(2)}return {packet.name}._from_dict(data)")
        
        lines.append("")
        lines.append(f'{self._i()}raise ValueError(f"Unknown packet type: {{packet_type}}")')
        
        return "\n".join(lines)
    
    def generate_security_utils(self) -> str:
        """Generate security_utils.py with validation utilities."""
        lines = [
            '"""',
            'CrossPacket Security Utilities',
            '',
            'Provides validation functions for securing packet data:',
            '- ValidationError: Exception for validation failures',
            '- SecurityLimits: Configurable limits for validation',
            '- validate_int: Integer bounds checking',
            '- validate_float: Float validation (NaN/Infinity handling)',
            '- validate_string: String length limits',
            '- validate_list: List size limits',
            '- validate_map: Map size limits',
            '- validate_required_fields: Required field checking',
            '"""',
            'from __future__ import annotations',
            '',
            'from dataclasses import dataclass, field',
            'from typing import Any, Callable, Dict, List, Optional, TypeVar',
            'import math',
            '',
            '',
            'class ValidationError(Exception):',
            f'{self._i()}"""Exception raised when validation fails."""',
            '',
            f'{self._i()}def __init__(self, field: str, message: str, value: Any = None):',
            f'{self._i(2)}"""',
            f'{self._i(2)}Initialize a validation error.',
            f'{self._i(2)}',
            f'{self._i(2)}Args:',
            f'{self._i(3)}field: Name of the field that failed validation',
            f'{self._i(3)}message: Human-readable error message',
            f'{self._i(3)}value: The invalid value (optional)',
            f'{self._i(2)}"""',
            f'{self._i(2)}self.field = field',
            f'{self._i(2)}self.message = message',
            f'{self._i(2)}self.value = value',
            f'{self._i(2)}super().__init__(f"{{field}}: {{message}}")',
            '',
            f'{self._i()}def __repr__(self) -> str:',
            f'{self._i(2)}return f"ValidationError(field={{self.field!r}}, message={{self.message!r}})"',
            '',
            '',
            '@dataclass',
            'class SecurityLimits:',
            f'{self._i()}"""',
            f'{self._i()}Configurable limits for packet validation.',
            f'{self._i()}',
            f'{self._i()}Attributes:',
            f'{self._i(2)}max_int: Maximum allowed integer value (default: 2^63-1)',
            f'{self._i(2)}min_int: Minimum allowed integer value (default: -2^63)',
            f'{self._i(2)}max_list_size: Maximum number of items in a list (default: 100000)',
            f'{self._i(2)}max_map_size: Maximum number of keys in a map (default: 100000)',
            f'{self._i(2)}max_string_length: Maximum string length in characters (default: 10MB)',
            f'{self._i(2)}max_bytes_length: Maximum bytes length (default: 100MB)',
            f'{self._i(2)}allow_nan: Whether to allow NaN float values (default: True)',
            f'{self._i(2)}allow_infinity: Whether to allow Infinity float values (default: True)',
            f'{self._i()}"""',
            '',
            f'{self._i()}max_int: int = 9223372036854775807  # 2^63 - 1',
            f'{self._i()}min_int: int = -9223372036854775808  # -2^63',
            f'{self._i()}max_list_size: int = 100000',
            f'{self._i()}max_map_size: int = 100000',
            f'{self._i()}max_string_length: int = 10000000  # 10MB',
            f'{self._i()}max_bytes_length: int = 100000000  # 100MB',
            f'{self._i()}allow_nan: bool = True',
            f'{self._i()}allow_infinity: bool = True',
            '',
            '',
            '# Default global limits',
            'DEFAULT_LIMITS = SecurityLimits()',
            '',
            '',
            'def validate_int(',
            f'{self._i()}value: Any,',
            f'{self._i()}field_name: str,',
            f'{self._i()}limits: Optional[SecurityLimits] = None,',
            f'{self._i()}*,',
            f'{self._i()}min_val: Optional[int] = None,',
            f'{self._i()}max_val: Optional[int] = None,',
            f'{self._i()}allow_none: bool = False,',
            ') -> Optional[int]:',
            f'{self._i()}"""',
            f'{self._i()}Validate an integer value with bounds checking.',
            f'{self._i()}',
            f'{self._i()}Args:',
            f'{self._i(2)}value: The value to validate',
            f'{self._i(2)}field_name: Name of the field (for error messages)',
            f'{self._i(2)}limits: Security limits to apply (default: global limits)',
            f'{self._i(2)}min_val: Minimum allowed value (overrides limits.min_int)',
            f'{self._i(2)}max_val: Maximum allowed value (overrides limits.max_int)',
            f'{self._i(2)}allow_none: Whether None values are allowed',
            f'{self._i()}',
            f'{self._i()}Returns:',
            f'{self._i(2)}The validated integer value, or None if allow_none=True and value is None',
            f'{self._i()}',
            f'{self._i()}Raises:',
            f'{self._i(2)}ValidationError: If validation fails',
            f'{self._i()}"""',
            f'{self._i()}if value is None:',
            f'{self._i(2)}if allow_none:',
            f'{self._i(3)}return None',
            f'{self._i(2)}raise ValidationError(field_name, "Value is required", value)',
            '',
            f'{self._i()}if not isinstance(value, (int, float)) or isinstance(value, bool):',
            f'{self._i(2)}raise ValidationError(field_name, f"Expected int, got {{type(value).__name__}}", value)',
            '',
            f'{self._i()}int_value = int(value)',
            f'{self._i()}limits = limits or DEFAULT_LIMITS',
            '',
            f'{self._i()}effective_min = min_val if min_val is not None else limits.min_int',
            f'{self._i()}effective_max = max_val if max_val is not None else limits.max_int',
            '',
            f'{self._i()}if int_value < effective_min:',
            f'{self._i(2)}raise ValidationError(field_name, f"Value {{int_value}} is less than minimum {{effective_min}}", value)',
            '',
            f'{self._i()}if int_value > effective_max:',
            f'{self._i(2)}raise ValidationError(field_name, f"Value {{int_value}} exceeds maximum {{effective_max}}", value)',
            '',
            f'{self._i()}return int_value',
            '',
            '',
            'def validate_float(',
            f'{self._i()}value: Any,',
            f'{self._i()}field_name: str,',
            f'{self._i()}limits: Optional[SecurityLimits] = None,',
            f'{self._i()}*,',
            f'{self._i()}min_val: Optional[float] = None,',
            f'{self._i()}max_val: Optional[float] = None,',
            f'{self._i()}allow_none: bool = False,',
            f'{self._i()}allow_nan: Optional[bool] = None,',
            f'{self._i()}allow_infinity: Optional[bool] = None,',
            ') -> Optional[float]:',
            f'{self._i()}"""',
            f'{self._i()}Validate a float value with NaN/Infinity handling.',
            f'{self._i()}',
            f'{self._i()}Args:',
            f'{self._i(2)}value: The value to validate',
            f'{self._i(2)}field_name: Name of the field (for error messages)',
            f'{self._i(2)}limits: Security limits to apply (default: global limits)',
            f'{self._i(2)}min_val: Minimum allowed value',
            f'{self._i(2)}max_val: Maximum allowed value',
            f'{self._i(2)}allow_none: Whether None values are allowed',
            f'{self._i(2)}allow_nan: Whether NaN is allowed (overrides limits)',
            f'{self._i(2)}allow_infinity: Whether Infinity is allowed (overrides limits)',
            f'{self._i()}',
            f'{self._i()}Returns:',
            f'{self._i(2)}The validated float value',
            f'{self._i()}',
            f'{self._i()}Raises:',
            f'{self._i(2)}ValidationError: If validation fails',
            f'{self._i()}"""',
            f'{self._i()}if value is None:',
            f'{self._i(2)}if allow_none:',
            f'{self._i(3)}return None',
            f'{self._i(2)}raise ValidationError(field_name, "Value is required", value)',
            '',
            f'{self._i()}if not isinstance(value, (int, float)) or isinstance(value, bool):',
            f'{self._i(2)}raise ValidationError(field_name, f"Expected float, got {{type(value).__name__}}", value)',
            '',
            f'{self._i()}float_value = float(value)',
            f'{self._i()}limits = limits or DEFAULT_LIMITS',
            '',
            f'{self._i()}effective_allow_nan = allow_nan if allow_nan is not None else limits.allow_nan',
            f'{self._i()}effective_allow_infinity = allow_infinity if allow_infinity is not None else limits.allow_infinity',
            '',
            f'{self._i()}if math.isnan(float_value) and not effective_allow_nan:',
            f'{self._i(2)}raise ValidationError(field_name, "NaN values are not allowed", value)',
            '',
            f'{self._i()}if math.isinf(float_value) and not effective_allow_infinity:',
            f'{self._i(2)}raise ValidationError(field_name, "Infinity values are not allowed", value)',
            '',
            f'{self._i()}if min_val is not None and float_value < min_val:',
            f'{self._i(2)}raise ValidationError(field_name, f"Value {{float_value}} is less than minimum {{min_val}}", value)',
            '',
            f'{self._i()}if max_val is not None and float_value > max_val:',
            f'{self._i(2)}raise ValidationError(field_name, f"Value {{float_value}} exceeds maximum {{max_val}}", value)',
            '',
            f'{self._i()}return float_value',
            '',
            '',
            'def validate_string(',
            f'{self._i()}value: Any,',
            f'{self._i()}field_name: str,',
            f'{self._i()}limits: Optional[SecurityLimits] = None,',
            f'{self._i()}*,',
            f'{self._i()}min_length: Optional[int] = None,',
            f'{self._i()}max_length: Optional[int] = None,',
            f'{self._i()}allow_none: bool = False,',
            f'{self._i()}allow_empty: bool = True,',
            f'{self._i()}pattern: Optional[str] = None,',
            ') -> Optional[str]:',
            f'{self._i()}"""',
            f'{self._i()}Validate a string value with length limits.',
            f'{self._i()}',
            f'{self._i()}Args:',
            f'{self._i(2)}value: The value to validate',
            f'{self._i(2)}field_name: Name of the field (for error messages)',
            f'{self._i(2)}limits: Security limits to apply (default: global limits)',
            f'{self._i(2)}min_length: Minimum string length',
            f'{self._i(2)}max_length: Maximum string length (overrides limits.max_string_length)',
            f'{self._i(2)}allow_none: Whether None values are allowed',
            f'{self._i(2)}allow_empty: Whether empty strings are allowed',
            f'{self._i(2)}pattern: Regex pattern to match (optional)',
            f'{self._i()}',
            f'{self._i()}Returns:',
            f'{self._i(2)}The validated string value',
            f'{self._i()}',
            f'{self._i()}Raises:',
            f'{self._i(2)}ValidationError: If validation fails',
            f'{self._i()}"""',
            f'{self._i()}if value is None:',
            f'{self._i(2)}if allow_none:',
            f'{self._i(3)}return None',
            f'{self._i(2)}raise ValidationError(field_name, "Value is required", value)',
            '',
            f'{self._i()}if not isinstance(value, str):',
            f'{self._i(2)}raise ValidationError(field_name, f"Expected string, got {{type(value).__name__}}", value)',
            '',
            f'{self._i()}limits = limits or DEFAULT_LIMITS',
            f'{self._i()}effective_max = max_length if max_length is not None else limits.max_string_length',
            '',
            f'{self._i()}if not allow_empty and len(value) == 0:',
            f'{self._i(2)}raise ValidationError(field_name, "Empty string not allowed", value)',
            '',
            f'{self._i()}if min_length is not None and len(value) < min_length:',
            f'{self._i(2)}raise ValidationError(field_name, f"String length {{len(value)}} is less than minimum {{min_length}}", value)',
            '',
            f'{self._i()}if len(value) > effective_max:',
            f'{self._i(2)}raise ValidationError(field_name, f"String length {{len(value)}} exceeds maximum {{effective_max}}", value)',
            '',
            f'{self._i()}if pattern is not None:',
            f'{self._i(2)}import re',
            f'{self._i(2)}if not re.match(pattern, value):',
            f'{self._i(3)}raise ValidationError(field_name, f"String does not match pattern: {{pattern}}", value)',
            '',
            f'{self._i()}return value',
            '',
            '',
            'T = TypeVar("T")',
            '',
            '',
            'def validate_list(',
            f'{self._i()}value: Any,',
            f'{self._i()}field_name: str,',
            f'{self._i()}limits: Optional[SecurityLimits] = None,',
            f'{self._i()}*,',
            f'{self._i()}min_size: Optional[int] = None,',
            f'{self._i()}max_size: Optional[int] = None,',
            f'{self._i()}allow_none: bool = False,',
            f'{self._i()}item_validator: Optional[Callable[[Any, str], T]] = None,',
            ') -> Optional[List[Any]]:',
            f'{self._i()}"""',
            f'{self._i()}Validate a list with size limits.',
            f'{self._i()}',
            f'{self._i()}Args:',
            f'{self._i(2)}value: The value to validate',
            f'{self._i(2)}field_name: Name of the field (for error messages)',
            f'{self._i(2)}limits: Security limits to apply (default: global limits)',
            f'{self._i(2)}min_size: Minimum number of items',
            f'{self._i(2)}max_size: Maximum number of items (overrides limits.max_list_size)',
            f'{self._i(2)}allow_none: Whether None values are allowed',
            f'{self._i(2)}item_validator: Optional validator function for each item',
            f'{self._i()}',
            f'{self._i()}Returns:',
            f'{self._i(2)}The validated list',
            f'{self._i()}',
            f'{self._i()}Raises:',
            f'{self._i(2)}ValidationError: If validation fails',
            f'{self._i()}"""',
            f'{self._i()}if value is None:',
            f'{self._i(2)}if allow_none:',
            f'{self._i(3)}return None',
            f'{self._i(2)}raise ValidationError(field_name, "Value is required", value)',
            '',
            f'{self._i()}if not isinstance(value, list):',
            f'{self._i(2)}raise ValidationError(field_name, f"Expected list, got {{type(value).__name__}}", value)',
            '',
            f'{self._i()}limits = limits or DEFAULT_LIMITS',
            f'{self._i()}effective_max = max_size if max_size is not None else limits.max_list_size',
            '',
            f'{self._i()}if min_size is not None and len(value) < min_size:',
            f'{self._i(2)}raise ValidationError(field_name, f"List size {{len(value)}} is less than minimum {{min_size}}", value)',
            '',
            f'{self._i()}if len(value) > effective_max:',
            f'{self._i(2)}raise ValidationError(field_name, f"List size {{len(value)}} exceeds maximum {{effective_max}}", value)',
            '',
            f'{self._i()}if item_validator:',
            f'{self._i(2)}validated = []',
            f'{self._i(2)}for i, item in enumerate(value):',
            f'{self._i(3)}validated.append(item_validator(item, f"{{field_name}}[{{i}}]"))',
            f'{self._i(2)}return validated',
            '',
            f'{self._i()}return list(value)',
            '',
            '',
            'def validate_map(',
            f'{self._i()}value: Any,',
            f'{self._i()}field_name: str,',
            f'{self._i()}limits: Optional[SecurityLimits] = None,',
            f'{self._i()}*,',
            f'{self._i()}min_size: Optional[int] = None,',
            f'{self._i()}max_size: Optional[int] = None,',
            f'{self._i()}allow_none: bool = False,',
            f'{self._i()}key_validator: Optional[Callable[[Any, str], Any]] = None,',
            f'{self._i()}value_validator: Optional[Callable[[Any, str], Any]] = None,',
            ') -> Optional[Dict[Any, Any]]:',
            f'{self._i()}"""',
            f'{self._i()}Validate a map/dict with size limits.',
            f'{self._i()}',
            f'{self._i()}Args:',
            f'{self._i(2)}value: The value to validate',
            f'{self._i(2)}field_name: Name of the field (for error messages)',
            f'{self._i(2)}limits: Security limits to apply (default: global limits)',
            f'{self._i(2)}min_size: Minimum number of keys',
            f'{self._i(2)}max_size: Maximum number of keys (overrides limits.max_map_size)',
            f'{self._i(2)}allow_none: Whether None values are allowed',
            f'{self._i(2)}key_validator: Optional validator function for keys',
            f'{self._i(2)}value_validator: Optional validator function for values',
            f'{self._i()}',
            f'{self._i()}Returns:',
            f'{self._i(2)}The validated map',
            f'{self._i()}',
            f'{self._i()}Raises:',
            f'{self._i(2)}ValidationError: If validation fails',
            f'{self._i()}"""',
            f'{self._i()}if value is None:',
            f'{self._i(2)}if allow_none:',
            f'{self._i(3)}return None',
            f'{self._i(2)}raise ValidationError(field_name, "Value is required", value)',
            '',
            f'{self._i()}if not isinstance(value, dict):',
            f'{self._i(2)}raise ValidationError(field_name, f"Expected dict, got {{type(value).__name__}}", value)',
            '',
            f'{self._i()}limits = limits or DEFAULT_LIMITS',
            f'{self._i()}effective_max = max_size if max_size is not None else limits.max_map_size',
            '',
            f'{self._i()}if min_size is not None and len(value) < min_size:',
            f'{self._i(2)}raise ValidationError(field_name, f"Map size {{len(value)}} is less than minimum {{min_size}}", value)',
            '',
            f'{self._i()}if len(value) > effective_max:',
            f'{self._i(2)}raise ValidationError(field_name, f"Map size {{len(value)}} exceeds maximum {{effective_max}}", value)',
            '',
            f'{self._i()}if key_validator or value_validator:',
            f'{self._i(2)}validated = {{}}',
            f'{self._i(2)}for k, v in value.items():',
            f'{self._i(3)}validated_key = key_validator(k, f"{{field_name}}.key") if key_validator else k',
            f'{self._i(3)}validated_value = value_validator(v, f"{{field_name}}[{{k!r}}]") if value_validator else v',
            f'{self._i(3)}validated[validated_key] = validated_value',
            f'{self._i(2)}return validated',
            '',
            f'{self._i()}return dict(value)',
            '',
            '',
            'def validate_required_fields(',
            f'{self._i()}data: Dict[str, Any],',
            f'{self._i()}required_fields: List[str],',
            f'{self._i()}packet_name: str,',
            ') -> None:',
            f'{self._i()}"""',
            f'{self._i()}Validate that all required fields are present in data.',
            f'{self._i()}',
            f'{self._i()}Args:',
            f'{self._i(2)}data: The data dictionary to check',
            f'{self._i(2)}required_fields: List of field names that must be present',
            f'{self._i(2)}packet_name: Name of the packet (for error messages)',
            f'{self._i()}',
            f'{self._i()}Raises:',
            f'{self._i(2)}ValidationError: If any required fields are missing',
            f'{self._i()}"""',
            f'{self._i()}if not isinstance(data, dict):',
            f'{self._i(2)}raise ValidationError("data", f"Expected dict for {{packet_name}}, got {{type(data).__name__}}", data)',
            '',
            f'{self._i()}missing = [f for f in required_fields if f not in data]',
            f'{self._i()}if missing:',
            f'{self._i(2)}missing_str = ", ".join(missing)',
            f'{self._i(2)}raise ValidationError(',
            f'{self._i(3)}"required_fields",',
            f'{self._i(3)}f"Missing required fields in {{packet_name}}: {{missing_str}}",',
            f'{self._i(3)}missing,',
            f'{self._i(2)})',
            '',
        ]
        
        return "\n".join(lines)
    
    def generate(self, packets: List[PacketDefinition], override: bool = False, clean: bool = False, no_msgpack: bool = False, no_json: bool = False, type_field: str = "packetType"):
        """Generate all Python files."""
        self.type_field = type_field
        self.no_msgpack = no_msgpack
        self.no_json = no_json
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if clean:
            for file in self.output_dir.glob("*.py"):
                file.unlink()
        
        # Generate security_utils.py
        security_path = self.output_dir / "security_utils.py"
        if not security_path.exists() or override:
            security_path.write_text(self.generate_security_utils())
            print(f"Generated: {security_path}")
        
        # Generate __init__.py
        init_path = self.output_dir / "__init__.py"
        if not init_path.exists() or override:
            init_path.write_text(self.generate_init(packets))
            print(f"Generated: {init_path}")
        
        # Generate individual packets
        for packet in packets:
            filename = to_snake_case(packet.name) + ".py"
            filepath = self.output_dir / filename
            if not filepath.exists() or override:
                filepath.write_text(self.generate_packet(packet))
                print(f"Generated: {filepath}")
            else:
                print(f"Skipped (exists): {filepath}")


class JavaGenerator:
    """Generates Java packet code."""
    
    def __init__(self, config: Dict[str, Any]):
        self.output_dir = Path(config.get("output_dir", "./generated/java"))
        self.package = config.get("package", "com.crosspacket")
        self.indent = config.get("indent", "    ")  # Java: 4 spaces
    
    def _i(self, level: int = 1) -> str:
        """Return indentation for the given level."""
        return self.indent * level
    
    def java_type(self, field: PacketField) -> str:
        """Get Java type for a field."""
        return TYPE_MAPPINGS.get(field.type, {}).get("java", "Object")
    
    def java_boxed_type(self, field: PacketField) -> str:
        """Get Java boxed type for a field (for generics/nullability)."""
        type_map = {
            "int": "Long",
            "float": "Double",
            "double": "Double",
            "bool": "Boolean",
            "string": "String",
            "datetime": "ZonedDateTime",
            "time": "LocalTime",
            "bytes": "byte[]",
            "list": "List<Object>",
            "list_int": "List<Long>",
            "list_string": "List<String>",
            "map": "Map<String, Object>",
            "embedded_map": "Map<Object, Object>",
            "map_string_dynamic": "Map<String, Object>",
        }
        return type_map.get(field.type, "Object")
    
    def generate_packet(self, packet: PacketDefinition) -> str:
        """Generate Java code for a packet."""
        lines = []
        
        # Package and imports
        lines.append(f"package {self.package};")
        lines.append("")
        lines.append("import java.time.ZonedDateTime;")
        lines.append("import java.time.LocalTime;")
        lines.append("import java.time.format.DateTimeFormatter;")
        lines.append("import java.util.*;")
        lines.append("import com.fasterxml.jackson.databind.ObjectMapper;")
        lines.append("import org.msgpack.core.*;")
        lines.append("")
        
        # Class javadoc
        if packet.description:
            lines.append("/**")
            lines.append(f" * {packet.description}")
            lines.append(" */")
        
        # Class definition
        lines.append(f"public class {packet.name} extends DataPacket {{")
        lines.append("")
        
        # Type constant
        lines.append(f'{self._i()}public static final String TYPE = "{packet.path}";')
        lines.append("")
        
        # Fields
        for field in packet.fields:
            java_type = self.java_type(field)
            field_name = to_camel_case(field.name)
            lines.append(f"{self._i()}private {java_type} {field_name};")
        
        lines.append("")
        
        # Default constructor
        lines.append(f"{self._i()}public {packet.name}() {{}}")
        lines.append("")
        
        # Parameterized constructor
        if packet.fields:
            params = []
            for field in packet.fields:
                java_type = self.java_type(field)
                field_name = to_camel_case(field.name)
                params.append(f"{java_type} {field_name}")
            lines.append(f"{self._i()}public {packet.name}({', '.join(params)}) {{")
            for field in packet.fields:
                field_name = to_camel_case(field.name)
                lines.append(f"{self._i(2)}this.{field_name} = {field_name};")
            lines.append(f"{self._i()}}}")
            lines.append("")
        
        # Getters and setters
        for field in packet.fields:
            java_type = self.java_type(field)
            field_name = to_camel_case(field.name)
            pascal_name = to_pascal_case(field.name)
            
            # Getter
            lines.append(f"{self._i()}public {java_type} get{pascal_name}() {{")
            lines.append(f"{self._i(2)}return {field_name};")
            lines.append(f"{self._i()}}}")
            lines.append("")
            
            # Setter
            lines.append(f"{self._i()}public void set{pascal_name}({java_type} {field_name}) {{")
            lines.append(f"{self._i(2)}this.{field_name} = {field_name};")
            lines.append(f"{self._i()}}}")
            lines.append("")
        
        # getType method
        lines.append(f"{self._i()}@Override")
        lines.append(f"{self._i()}public String getType() {{")
        lines.append(f"{self._i(2)}return TYPE;")
        lines.append(f"{self._i()}}}")
        lines.append("")
        
        # toMap method (protected - internal helper)
        lines.append(f"{self._i()}@Override")
        lines.append(f"{self._i()}protected Map<String, Object> toMap() {{")
        lines.append(f"{self._i(2)}Map<String, Object> map = new HashMap<>();")
        lines.append(f'{self._i(2)}map.put("{self.type_field}", TYPE);')
        for field in packet.fields:
            field_name = to_camel_case(field.name)
            if field.type == "datetime":
                lines.append(f'{self._i(2)}map.put("{field.name}", {field_name} != null ? {field_name}.format(DateTimeFormatter.ISO_OFFSET_DATE_TIME) : null);')
            elif field.type == "time":
                lines.append(f'{self._i(2)}map.put("{field.name}", {field_name} != null ? {field_name}.toString() : null);')
            else:
                lines.append(f'{self._i(2)}map.put("{field.name}", {field_name});')
        lines.append(f"{self._i(2)}return map;")
        lines.append(f"{self._i()}}}")
        lines.append("")
        
        # toJson is INHERITED from DataPacket (uses shared ObjectMapper for efficiency)
        # The base class toJson() calls toMap() which is abstract and implemented above.
        # No need to generate a redundant toJson() here - it's already in DataPacket.
        
        # toMsgPack method
        if not self.no_msgpack:
            lines.append(f"{self._i()}public byte[] toMsgPack() throws Exception {{")
            lines.append(f"{self._i(2)}MessageBufferPacker packer = MessagePack.newDefaultBufferPacker();")
            lines.append(f"{self._i(2)}packer.packMapHeader({len(packet.fields) + 1});")
            lines.append(f'{self._i(2)}packer.packString("{self.type_field}");')
            lines.append(f"{self._i(2)}packer.packString(TYPE);")
            for field in packet.fields:
                field_name = to_camel_case(field.name)
                lines.append(f'{self._i(2)}packer.packString("{field.name}");')
                if field.type in ['int']:
                    lines.append(f"{self._i(2)}packer.packLong({field_name});")
                elif field.type in ['float', 'double']:
                    lines.append(f"{self._i(2)}packer.packDouble({field_name});")
                elif field.type == 'bool':
                    lines.append(f"{self._i(2)}packer.packBoolean({field_name});")
                elif field.type == 'string':
                    lines.append(f"{self._i(2)}if ({field_name} != null) packer.packString({field_name}); else packer.packNil();")
                elif field.type in ['datetime', 'time']:
                    lines.append(f"{self._i(2)}if ({field_name} != null) packer.packString({field_name}.toString()); else packer.packNil();")
                elif field.type == 'bytes':
                    lines.append(f"{self._i(2)}if ({field_name} != null) {{ packer.packBinaryHeader({field_name}.length); packer.writePayload({field_name}); }} else packer.packNil();")
                elif field.type in ['list', 'list_int', 'list_string']:
                    lines.append(f"{self._i(2)}if ({field_name} != null) {{ packList(packer, {field_name}); }} else packer.packNil();")
                elif field.type in ['map', 'embedded_map', 'map_string_dynamic']:
                    lines.append(f"{self._i(2)}if ({field_name} != null) {{ packMap(packer, {field_name}); }} else packer.packNil();")
                else:
                    lines.append(f"{self._i(2)}packer.packNil(); // Unknown type: {field.type}")
            lines.append(f"{self._i(2)}packer.close();")
            lines.append(f"{self._i(2)}return packer.toByteArray();")
            lines.append(f"{self._i()}}}")
            lines.append("")
            
            # fromMsgPack method - utility methods are now inherited from DataPacket
            lines.append(f"{self._i()}public static {packet.name} fromMsgPack(byte[] data) throws Exception {{")
            lines.append(f"{self._i(2)}MessageUnpacker unpacker = MessagePack.newDefaultUnpacker(data);")
            lines.append(f"{self._i(2)}Map<String, Object> map = new HashMap<>();")
            lines.append(f"{self._i(2)}int size = unpacker.unpackMapHeader();")
            lines.append(f"{self._i(2)}for (int i = 0; i < size; i++) {{")
            lines.append(f"{self._i(3)}String key = unpacker.unpackString();")
            lines.append(f"{self._i(3)}map.put(key, unpackValue(unpacker));")
            lines.append(f"{self._i(2)}}}")
            lines.append(f"{self._i(2)}unpacker.close();")
            lines.append(f"{self._i(2)}return fromMap(map);")
            lines.append(f"{self._i()}}}")
            lines.append("")
        
        # fromMap private static method (internal helper)
        lines.append(f"{self._i()}private static {packet.name} fromMap(Map<String, Object> map) {{")
        lines.append(f"{self._i(2)}{packet.name} packet = new {packet.name}();")
        for field in packet.fields:
            field_name = to_camel_case(field.name)
            pascal_name = to_pascal_case(field.name)
            if field.type == "datetime":
                lines.append(f'{self._i(2)}Object {field_name}Val = map.get("{field.name}");')
                lines.append(f"{self._i(2)}if ({field_name}Val != null) packet.set{pascal_name}(ZonedDateTime.parse({field_name}Val.toString()));")
            elif field.type == "time":
                lines.append(f'{self._i(2)}Object {field_name}Val = map.get("{field.name}");')
                lines.append(f"{self._i(2)}if ({field_name}Val != null) packet.set{pascal_name}(LocalTime.parse({field_name}Val.toString()));")
            elif field.type == "int":
                lines.append(f'{self._i(2)}packet.set{pascal_name}(((Number) map.get("{field.name}")).longValue());')
            elif field.type in ["float", "double"]:
                lines.append(f'{self._i(2)}packet.set{pascal_name}(((Number) map.get("{field.name}")).doubleValue());')
            elif field.type == "bool":
                lines.append(f'{self._i(2)}packet.set{pascal_name}((Boolean) map.get("{field.name}"));')
            elif field.type == "string":
                lines.append(f'{self._i(2)}packet.set{pascal_name}((String) map.get("{field.name}"));')
            elif field.type == "bytes":
                # Handle bytes - can come as byte[] from msgpack or String (Base64) from JSON
                lines.append(f'{self._i(2)}Object {field_name}Val = map.get("{field.name}");')
                lines.append(f"{self._i(2)}if ({field_name}Val instanceof byte[]) {{")
                lines.append(f"{self._i(3)}packet.set{pascal_name}((byte[]) {field_name}Val);")
                lines.append(f"{self._i(2)}}} else if ({field_name}Val instanceof String) {{")
                lines.append(f"{self._i(3)}packet.set{pascal_name}(java.util.Base64.getDecoder().decode((String) {field_name}Val));")
                lines.append(f"{self._i(2)}}}")
            elif field.type in ["list_int", "list_string"]:
                # Handle typed lists with proper casting
                lines.append(f'{self._i(2)}packet.set{pascal_name}(({self.java_boxed_type(field)}) map.get("{field.name}"));')
            else:
                lines.append(f'{self._i(2)}packet.set{pascal_name}(({self.java_boxed_type(field)}) map.get("{field.name}"));')
        lines.append(f"{self._i(2)}return packet;")
        lines.append(f"{self._i()}}}")
        lines.append("")
        
        # fromJson static method
        if not self.no_json:
            lines.append(f"{self._i()}public static {packet.name} fromJson(String json) throws Exception {{")
            lines.append(f"{self._i(2)}ObjectMapper mapper = new ObjectMapper();")
            lines.append(f"{self._i(2)}@SuppressWarnings(\"unchecked\")")
            lines.append(f"{self._i(2)}Map<String, Object> map = mapper.readValue(json, Map.class);")
            lines.append(f"{self._i(2)}return fromMap(map);")
            lines.append(f"{self._i()}}}")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_base_class(self) -> str:
        """Generate base DataPacket class with shared MsgPack utilities."""
        lines = [
            f"package {self.package};",
            "",
            "import java.util.*;",
            "import com.fasterxml.jackson.databind.ObjectMapper;",
            "import org.msgpack.core.*;",
            "",
            "/**",
            " * Base class for all data packets.",
            " */",
            "public abstract class DataPacket {",
            "",
            f"{self._i()}private static final ObjectMapper mapper = new ObjectMapper();",
            "",
            f"{self._i()}/**",
            f"{self._i()} * Get the packet type identifier.",
            f"{self._i()} */",
            f"{self._i()}public abstract String getType();",
            "",
            f"{self._i()}/**",
            f"{self._i()} * Convert to Map for serialization (internal).",
            f"{self._i()} */",
            f"{self._i()}protected abstract Map<String, Object> toMap();",
            "",
            f"{self._i()}/**",
            f"{self._i()} * Serialize to JSON string.",
            f"{self._i()} */",
            f"{self._i()}public String toJson() throws Exception {{",
            f"{self._i(2)}return mapper.writeValueAsString(toMap());",
            f"{self._i()}}}",
            "",
            f"{self._i()}// =========== Shared MsgPack utilities ===========",
            "",
            f"{self._i()}protected static void packList(MessageBufferPacker packer, List<?> list) throws Exception {{",
            f"{self._i(2)}packer.packArrayHeader(list.size());",
            f"{self._i(2)}for (Object item : list) {{",
            f"{self._i(3)}packValue(packer, item);",
            f"{self._i(2)}}}",
            f"{self._i()}}}",
            "",
            f"{self._i()}protected static void packMap(MessageBufferPacker packer, Map<?, ?> map) throws Exception {{",
            f"{self._i(2)}packer.packMapHeader(map.size());",
            f"{self._i(2)}for (Map.Entry<?, ?> entry : map.entrySet()) {{",
            f"{self._i(3)}packValue(packer, entry.getKey());",
            f"{self._i(3)}packValue(packer, entry.getValue());",
            f"{self._i(2)}}}",
            f"{self._i()}}}",
            "",
            f"{self._i()}protected static void packValue(MessageBufferPacker packer, Object value) throws Exception {{",
            f"{self._i(2)}if (value == null) {{ packer.packNil(); }}",
            f"{self._i(2)}else if (value instanceof String) {{ packer.packString((String) value); }}",
            f"{self._i(2)}else if (value instanceof Long) {{ packer.packLong((Long) value); }}",
            f"{self._i(2)}else if (value instanceof Integer) {{ packer.packInt((Integer) value); }}",
            f"{self._i(2)}else if (value instanceof Double) {{ packer.packDouble((Double) value); }}",
            f"{self._i(2)}else if (value instanceof Float) {{ packer.packFloat((Float) value); }}",
            f"{self._i(2)}else if (value instanceof Boolean) {{ packer.packBoolean((Boolean) value); }}",
            f"{self._i(2)}else if (value instanceof byte[]) {{ byte[] b = (byte[]) value; packer.packBinaryHeader(b.length); packer.writePayload(b); }}",
            f"{self._i(2)}else if (value instanceof List) {{ packList(packer, (List<?>) value); }}",
            f"{self._i(2)}else if (value instanceof Map) {{ packMap(packer, (Map<?, ?>) value); }}",
            f"{self._i(2)}else {{ packer.packString(value.toString()); }}",
            f"{self._i()}}}",
            "",
            f"{self._i()}protected static Object unpackValue(MessageUnpacker unpacker) throws Exception {{",
            f"{self._i(2)}MessageFormat format = unpacker.getNextFormat();",
            f"{self._i(2)}switch (format.getValueType()) {{",
            f"{self._i(3)}case STRING: return unpacker.unpackString();",
            f"{self._i(3)}case INTEGER: return unpacker.unpackLong();",
            f"{self._i(3)}case FLOAT: return unpacker.unpackDouble();",
            f"{self._i(3)}case BOOLEAN: return unpacker.unpackBoolean();",
            f"{self._i(3)}case NIL: unpacker.unpackNil(); return null;",
            f"{self._i(3)}case BINARY: {{",
            f"{self._i(4)}int len = unpacker.unpackBinaryHeader();",
            f"{self._i(4)}byte[] bytes = new byte[len];",
            f"{self._i(4)}unpacker.readPayload(bytes);",
            f"{self._i(4)}return bytes;",
            f"{self._i(3)}}}",
            f"{self._i(3)}case ARRAY: {{",
            f"{self._i(4)}int len = unpacker.unpackArrayHeader();",
            f"{self._i(4)}List<Object> list = new ArrayList<>(len);",
            f"{self._i(4)}for (int j = 0; j < len; j++) {{ list.add(unpackValue(unpacker)); }}",
            f"{self._i(4)}return list;",
            f"{self._i(3)}}}",
            f"{self._i(3)}case MAP: {{",
            f"{self._i(4)}int len = unpacker.unpackMapHeader();",
            f"{self._i(4)}Map<Object, Object> m = new HashMap<>(len);",
            f"{self._i(4)}for (int j = 0; j < len; j++) {{ m.put(unpackValue(unpacker), unpackValue(unpacker)); }}",
            f"{self._i(4)}return m;",
            f"{self._i(3)}}}",
            f"{self._i(3)}default: unpacker.skipValue(); return null;",
            f"{self._i(2)}}}",
            f"{self._i()}}}",
            "}",
        ]
        return "\n".join(lines)
    
    def generate(self, packets: List[PacketDefinition], override: bool = False, clean: bool = False, no_msgpack: bool = False, no_json: bool = False, type_field: str = "packetType"):
        """Generate all Java files."""
        self.type_field = type_field
        self.no_msgpack = no_msgpack
        self.no_json = no_json
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if clean:
            for file in self.output_dir.glob("*.java"):
                file.unlink()
        
        # Generate base class
        base_path = self.output_dir / "DataPacket.java"
        if not base_path.exists() or override:
            base_path.write_text(self.generate_base_class())
            print(f"Generated: {base_path}")
        
        # Generate individual packets
        for packet in packets:
            filepath = self.output_dir / f"{packet.name}.java"
            if not filepath.exists() or override:
                filepath.write_text(self.generate_packet(packet))
                print(f"Generated: {filepath}")
            else:
                print(f"Skipped (exists): {filepath}")


class TypeScriptGenerator:
    """Generates TypeScript packet code."""
    
    def __init__(self, config: Dict[str, Any]):
        self.output_dir = Path(config.get("output_dir", "./generated/typescript"))
        self.indent = config.get("indent", "  ")  # TypeScript: 2 spaces
    
    def _i(self, level: int = 1) -> str:
        """Return indentation for the given level."""
        return self.indent * level
    
    def ts_type(self, field: PacketField) -> str:
        """Get TypeScript type for a field."""
        base = TYPE_MAPPINGS.get(field.type, {}).get("typescript", "any")
        if field.optional:
            return f"{base} | null"
        return base
    
    def ts_json_type(self, field: PacketField) -> str:
        """Get TypeScript type for JSON data interface (dates are strings)."""
        if field.type == "datetime":
            base = "string"
        else:
            base = TYPE_MAPPINGS.get(field.type, {}).get("typescript", "any")
        if field.optional:
            return f"{base} | null"
        return base
    
    def ts_input_type(self, field: PacketField) -> str:
        """Get TypeScript type for input interface (accepts Date | string for datetime)."""
        if field.type == "datetime":
            base = "Date | string"
        else:
            base = TYPE_MAPPINGS.get(field.type, {}).get("typescript", "any")
        if field.optional:
            return f"{base} | null"
        return base
    
    def generate_packet(self, packet: PacketDefinition) -> str:
        """Generate TypeScript code for a packet."""
        lines = []
        
        # Header
        lines.append("// Auto-generated - do not modify manually")
        if not self.no_msgpack:
            lines.append("import * as msgpack from '@msgpack/msgpack';")
        lines.append("")
        
        # Serialized data interface (JSON-compatible types, dates are strings)
        lines.append(f"export interface {packet.name}Data {{")
        lines.append(f"{self._i()}{self.type_field}: string;")
        for field in packet.fields:
            ts_json_type = self.ts_json_type(field)
            lines.append(f"{self._i()}{to_camel_case(field.name)}: {ts_json_type};")
        lines.append("}")
        lines.append("")
        
        # Input interface (accepts Date | string for datetime - type-safe!)
        lines.append(f"export interface {packet.name}Input {{")
        for field in packet.fields:
            ts_input_type = self.ts_input_type(field)
            optional_marker = "?" if field.optional else ""
            lines.append(f"{self._i()}{to_camel_case(field.name)}{optional_marker}: {ts_input_type};")
        lines.append("}")
        lines.append("")
        
        # Class
        lines.append(f"export class {packet.name} {{")
        lines.append(f'{self._i()}static readonly TYPE = "{packet.path}";')
        lines.append("")
        
        # Properties
        for field in packet.fields:
            ts_type = self.ts_type(field)
            lines.append(f"{self._i()}{to_camel_case(field.name)}: {ts_type};")
        lines.append("")
        
        # Constructor - now uses properly typed Input interface
        lines.append(f"{self._i()}constructor(data: {packet.name}Input) {{")
        for field in packet.fields:
            camel_name = to_camel_case(field.name)
            if field.type == "datetime":
                if field.optional:
                    lines.append(f"{self._i(2)}this.{camel_name} = data.{camel_name} != null ? (data.{camel_name} instanceof Date ? data.{camel_name} : new Date(data.{camel_name})) : null;")
                else:
                    lines.append(f"{self._i(2)}this.{camel_name} = data.{camel_name} instanceof Date ? data.{camel_name} : new Date(data.{camel_name});")
            elif field.optional:
                lines.append(f"{self._i(2)}this.{camel_name} = data.{camel_name} ?? null;")
            else:
                lines.append(f"{self._i(2)}this.{camel_name} = data.{camel_name};")
        lines.append(f"{self._i()}}}")
        lines.append("")
        
        # Private _toData helper (used by toJSON and toMsgPack)
        # Note: No instanceof checks needed - constructor guarantees type invariants:
        # - datetime fields are always Date objects (not strings)
        # - optional datetime fields are Date | null (not string)
        lines.append(f"{self._i()}private _toData(): {packet.name}Data {{")
        lines.append(f"{self._i(2)}return {{")
        lines.append(f"{self._i(3)}{self.type_field}: {packet.name}.TYPE,")
        for field in packet.fields:
            camel_name = to_camel_case(field.name)
            if field.type == "datetime":
                if field.optional:
                    # Optional datetime: Date | null -> string | null
                    lines.append(f"{self._i(3)}{camel_name}: this.{camel_name}?.toISOString() ?? null,")
                else:
                    # Required datetime: Date -> string (constructor guarantees Date type)
                    lines.append(f"{self._i(3)}{camel_name}: this.{camel_name}.toISOString(),")
            else:
                lines.append(f"{self._i(3)}{camel_name}: this.{camel_name},")
        lines.append(f"{self._i(2)}}};")
        lines.append(f"{self._i()}}}")
        lines.append("")
        
        # Private _fromData helper (used by fromJSON and fromMsgPack)
        lines.append(f"{self._i()}private static _fromData(data: {packet.name}Data): {packet.name} {{")
        lines.append(f"{self._i(2)}return new {packet.name}({{")
        for field in packet.fields:
            camel_name = to_camel_case(field.name)
            if field.type == "datetime":
                if field.optional:
                    lines.append(f"{self._i(3)}{camel_name}: data.{camel_name} ? new Date(data.{camel_name}) : null,")
                else:
                    lines.append(f"{self._i(3)}{camel_name}: new Date(data.{camel_name}),")
            else:
                lines.append(f"{self._i(3)}{camel_name}: data.{camel_name},")
        lines.append(f"{self._i(2)}}});")
        lines.append(f"{self._i()}}}")
        lines.append("")
        
        # toJSON returns string (only if JSON enabled)
        if not self.no_json:
            lines.append(f"{self._i()}toJSON(): string {{")
            lines.append(f"{self._i(2)}return JSON.stringify(this._toData());")
            lines.append(f"{self._i()}}}")
            lines.append("")
            
            # fromJSON accepts string
            lines.append(f"{self._i()}static fromJSON(json: string): {packet.name} {{")
            lines.append(f"{self._i(2)}return {packet.name}._fromData(JSON.parse(json) as {packet.name}Data);")
            lines.append(f"{self._i()}}}")
            lines.append("")
        
        # toMsgPack (only if MsgPack enabled)
        if not self.no_msgpack:
            lines.append(f"{self._i()}toMsgPack(): Uint8Array {{")
            lines.append(f"{self._i(2)}return msgpack.encode(this._toData());")
            lines.append(f"{self._i()}}}")
            lines.append("")
            
            # fromMsgPack
            lines.append(f"{self._i()}static fromMsgPack(bytes: Uint8Array): {packet.name} {{")
            lines.append(f"{self._i(2)}const data = msgpack.decode(bytes) as {packet.name}Data;")
            lines.append(f"{self._i(2)}return {packet.name}._fromData(data);")
            lines.append(f"{self._i()}}}")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_index(self, packets: List[PacketDefinition]) -> str:
        """Generate index.ts with exports and deserializer."""
        lines = ["// Auto-generated - do not modify manually", ""]
        
        # Import all packets for the packetTypes map
        for packet in packets:
            filename = to_snake_case(packet.name)
            lines.append(f"import {{ {packet.name} }} from './{filename}';")
        lines.append("")
        
        # Re-export all packets
        for packet in packets:
            filename = to_snake_case(packet.name)
            lines.append(f"export {{ {packet.name} }} from './{filename}';")
        
        lines.append("")
        lines.append("// Packet type map for deserialization")
        lines.append("const packetTypes: Record<string, any> = {")
        for packet in packets:
            lines.append(f"{self._i()}'{packet.path}': {packet.name},")
        lines.append("};")
        lines.append("")
        lines.append("/**")
        lines.append(" * Deserialize a packet from parsed JSON data.")
        lines.append(" * @param data - The parsed JSON object with a packetType field")
        lines.append(" * @returns The deserialized packet instance")
        lines.append(" */")
        lines.append("export function deserializePacket(data: any): any {")
        lines.append(f"{self._i()}const PacketClass = packetTypes[data.{self.type_field}];")
        lines.append(f"{self._i()}if (!PacketClass) throw new Error(`Unknown packet type: ${{data.{self.type_field}}}`);")
        lines.append(f"{self._i()}return PacketClass._fromData(data);")
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate(self, packets: List[PacketDefinition], override: bool = False, clean: bool = False, no_msgpack: bool = False, no_json: bool = False, type_field: str = "packetType"):
        """Generate all TypeScript files."""
        self.type_field = type_field
        self.no_msgpack = no_msgpack
        self.no_json = no_json
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if clean:
            for file in self.output_dir.glob("*.ts"):
                file.unlink()
        
        # Generate index
        index_path = self.output_dir / "index.ts"
        if not index_path.exists() or override:
            index_path.write_text(self.generate_index(packets))
            print(f"Generated: {index_path}")
        
        # Generate individual packets
        for packet in packets:
            filename = to_snake_case(packet.name) + ".ts"
            filepath = self.output_dir / filename
            if not filepath.exists() or override:
                filepath.write_text(self.generate_packet(packet))
                print(f"Generated: {filepath}")
            else:
                print(f"Skipped (exists): {filepath}")


class RustGenerator:
    """Generates Rust packet code."""
    
    def __init__(self, config: Dict[str, Any]):
        self.output_dir = Path(config.get("output_dir", "./generated/rust"))
        self.indent = config.get("indent", "    ")  # Rust: 4 spaces
    
    def _i(self, level: int = 1) -> str:
        """Return indentation for the given level."""
        return self.indent * level
    
    def rust_type(self, field: PacketField) -> str:
        """Get Rust type for a field."""
        base = TYPE_MAPPINGS.get(field.type, {}).get("rust", "serde_json::Value")
        if field.optional:
            return f"Option<{base}>"
        return base
    
    def generate_packet(self, packet: PacketDefinition) -> str:
        """Generate Rust code for a packet."""
        lines = []
        
        # Header
        lines.append("// Auto-generated - do not modify manually")
        lines.append("use serde::{Deserialize, Serialize};")
        
        # Build chrono imports
        chrono_imports = []
        if packet.has_datetime():
            chrono_imports.extend(["DateTime", "Utc"])
        if packet.has_time():
            chrono_imports.append("NaiveTime")
        if chrono_imports:
            lines.append(f"use chrono::{{{', '.join(chrono_imports)}}};")
        
        # Only import HashMap if we have map fields
        if packet.has_map() or packet.has_embedded_map():
            lines.append("use std::collections::HashMap;")
        lines.append("")
        
        # Struct
        lines.append("#[derive(Debug, Clone, Serialize, Deserialize)]")
        lines.append(f"pub struct {packet.name} {{")
        
        # Always include type field
        lines.append(f'{self._i()}#[serde(rename = "{self.type_field}")]')
        lines.append(f"{self._i()}pub packet_type: String,")
        
        for field in packet.fields:
            rust_type = self.rust_type(field)
            lines.append(f"{self._i()}pub {field.name}: {rust_type},")
        lines.append("}")
        lines.append("")
        
        # Impl block
        lines.append(f"impl {packet.name} {{")
        lines.append(f'{self._i()}pub const TYPE: &\'static str = "{packet.path}";')
        lines.append("")
        
        # new constructor
        lines.append(f"{self._i()}pub fn new(")
        for field in packet.fields:
            rust_type = self.rust_type(field)
            lines.append(f"{self._i(2)}{field.name}: {rust_type},")
        lines.append(f"{self._i()}) -> Self {{")
        lines.append(f"{self._i(2)}Self {{")
        lines.append(f"{self._i(3)}packet_type: Self::TYPE.to_string(),")
        for field in packet.fields:
            lines.append(f"{self._i(3)}{field.name},")
        lines.append(f"{self._i(2)}}}")
        lines.append(f"{self._i()}}}")
        lines.append("")
        
        # to_json (only if JSON enabled)
        if not self.no_json:
            lines.append(f"{self._i()}pub fn to_json(&self) -> Result<String, serde_json::Error> {{")
            lines.append(f"{self._i(2)}serde_json::to_string(self)")
            lines.append(f"{self._i()}}}")
            lines.append("")
            
            # from_json
            lines.append(f"{self._i()}pub fn from_json(json: &str) -> Result<Self, serde_json::Error> {{")
            lines.append(f"{self._i(2)}serde_json::from_str(json)")
            lines.append(f"{self._i()}}}")
            lines.append("")
        
        # to_msgpack (only if MsgPack enabled)
        if not self.no_msgpack:
            lines.append(f"{self._i()}pub fn to_msgpack(&self) -> Result<Vec<u8>, rmp_serde::encode::Error> {{")
            lines.append(f"{self._i(2)}rmp_serde::to_vec(self)")
            lines.append(f"{self._i()}}}")
            lines.append("")
            
            # from_msgpack
            lines.append(f"{self._i()}pub fn from_msgpack(bytes: &[u8]) -> Result<Self, rmp_serde::decode::Error> {{")
            lines.append(f"{self._i(2)}rmp_serde::from_slice(bytes)")
            lines.append(f"{self._i()}}}")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def generate_mod(self, packets: List[PacketDefinition]) -> str:
        """Generate mod.rs with exports."""
        lines = ["// Auto-generated - do not modify manually", ""]
        
        for packet in packets:
            filename = to_snake_case(packet.name)
            lines.append(f"mod {filename};")
            lines.append(f"pub use {filename}::{packet.name};")
        
        return "\n".join(lines)
    
    def generate(self, packets: List[PacketDefinition], override: bool = False, clean: bool = False, no_msgpack: bool = False, no_json: bool = False, type_field: str = "packetType"):
        """Generate all Rust files."""
        self.type_field = type_field
        self.no_msgpack = no_msgpack
        self.no_json = no_json
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if clean:
            for file in self.output_dir.glob("*.rs"):
                file.unlink()
        
        # Generate Cargo.toml for the crate
        cargo_path = self.output_dir / "Cargo.toml"
        if not cargo_path.exists() or override:
            cargo_content = '''[package]
name = "crosspacket_generated"
version = "1.0.0"
edition = "2021"

[lib]
path = "mod.rs"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
rmp-serde = "1.3"
chrono = { version = "0.4", features = ["serde"] }
'''
            cargo_path.write_text(cargo_content)
            print(f"Generated: {cargo_path}")
        
        # Generate mod.rs
        mod_path = self.output_dir / "mod.rs"
        if not mod_path.exists() or override:
            mod_path.write_text(self.generate_mod(packets))
            print(f"Generated: {mod_path}")
        
        # Generate individual packets
        for packet in packets:
            filename = to_snake_case(packet.name) + ".rs"
            filepath = self.output_dir / filename
            if not filepath.exists() or override:
                filepath.write_text(self.generate_packet(packet))
                print(f"Generated: {filepath}")
            else:
                print(f"Skipped (exists): {filepath}")


class GoGenerator:
    """Generates Go packet code."""
    
    def __init__(self, config: Dict[str, Any]):
        self.output_dir = Path(config.get("output_dir", "./generated/go"))
        self.package = config.get("package", "packets")
        self.indent = "\t"  # Go uses tabs
    
    def _i(self, level: int = 1) -> str:
        """Return indentation for the given level."""
        return self.indent * level
    
    def go_type(self, field: PacketField) -> str:
        """Get Go type for a field."""
        base = TYPE_MAPPINGS.get(field.type, {}).get("go", "interface{}")
        if field.optional:
            # Go uses pointers for optional values
            if base in ["int64", "float64", "bool", "string"]:
                return f"*{base}"
        return base
    
    def generate_packet(self, packet: PacketDefinition) -> str:
        """Generate Go code for a packet."""
        lines = []
        
        # Header
        lines.append(f"package {self.package}")
        lines.append("")
        lines.append("import (")
        if not self.no_json:
            lines.append(f'{self._i()}"encoding/json"')
        if packet.has_datetime():
            lines.append(f'{self._i()}"time"')
        if not self.no_msgpack:
            lines.append(f'{self._i()}"github.com/vmihailenco/msgpack/v5"')
        lines.append(")")
        lines.append("")
        
        # Struct with appropriate tags
        lines.append(f"type {packet.name} struct {{")
        if not self.no_json and not self.no_msgpack:
            lines.append(f'{self._i()}Type string `json:\"{self.type_field}\" msgpack:\"{self.type_field}\"`')
        elif not self.no_json:
            lines.append(f'{self._i()}Type string `json:\"{self.type_field}\"`')
        elif not self.no_msgpack:
            lines.append(f'{self._i()}Type string `msgpack:\"{self.type_field}\"`')
        
        for field in packet.fields:
            go_type = self.go_type(field)
            pascal_name = to_pascal_case(field.name)
            if not self.no_json and not self.no_msgpack:
                lines.append(f'{self._i()}{pascal_name} {go_type} `json:"{field.name}" msgpack:"{field.name}"`')
            elif not self.no_json:
                lines.append(f'{self._i()}{pascal_name} {go_type} `json:"{field.name}"`')
            elif not self.no_msgpack:
                lines.append(f'{self._i()}{pascal_name} {go_type} `msgpack:"{field.name}"`')
        lines.append("}")
        lines.append("")
        
        # GetType method
        lines.append(f"func (p *{packet.name}) GetType() string {{")
        lines.append(f'{self._i()}return "{packet.path}"')
        lines.append("}")
        lines.append("")
        
        # ToJSON method (only if JSON enabled)
        if not self.no_json:
            lines.append(f"func (p *{packet.name}) ToJSON() ([]byte, error) {{")
            lines.append(f'{self._i()}p.Type = "{packet.path}"')
            lines.append(f"{self._i()}return json.Marshal(p)")
            lines.append("}")
            lines.append("")
            
            # FromJSON function
            lines.append(f"func {packet.name}FromJSON(data []byte) (*{packet.name}, error) {{")
            lines.append(f"{self._i()}var p {packet.name}")
            lines.append(f"{self._i()}err := json.Unmarshal(data, &p)")
            lines.append(f"{self._i()}return &p, err")
            lines.append("}")
            lines.append("")
        
        # ToMsgPack method (only if MsgPack enabled)
        if not self.no_msgpack:
            lines.append(f"func (p *{packet.name}) ToMsgPack() ([]byte, error) {{")
            lines.append(f'{self._i()}p.Type = "{packet.path}"')
            lines.append(f"{self._i()}return msgpack.Marshal(p)")
            lines.append("}")
            lines.append("")
            
            # FromMsgPack function
            lines.append(f"func {packet.name}FromMsgPack(data []byte) (*{packet.name}, error) {{")
            lines.append(f"{self._i()}var p {packet.name}")
            lines.append(f"{self._i()}err := msgpack.Unmarshal(data, &p)")
            lines.append(f"{self._i()}return &p, err")
            lines.append("}")
        
        return "\n".join(lines)
    
    def generate(self, packets: List[PacketDefinition], override: bool = False, clean: bool = False, no_msgpack: bool = False, no_json: bool = False, type_field: str = "packetType"):
        """Generate all Go files."""
        self.type_field = type_field
        self.no_msgpack = no_msgpack
        self.no_json = no_json
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if clean:
            for file in self.output_dir.glob("*.go"):
                file.unlink()
        
        # Generate individual packets
        for packet in packets:
            filename = to_snake_case(packet.name) + ".go"
            filepath = self.output_dir / filename
            if not filepath.exists() or override:
                filepath.write_text(self.generate_packet(packet))
                print(f"Generated: {filepath}")
            else:
                print(f"Skipped (exists): {filepath}")


class CppGenerator:
    """Generates C++ packet code with yyjson and msgpack-c support."""
    
    def __init__(self, config: Dict[str, Any]):
        self.output_dir = Path(config.get("output_dir", "./generated/cpp"))
        self.namespace = config.get("namespace", "packets")
        self.indent = config.get("indent", "    ")
    
    def _i(self, level: int = 1) -> str:
        """Return indentation for the given level."""
        return self.indent * level
    
    def cpp_type(self, field: PacketField) -> str:
        """Get C++ type for a field."""
        base = TYPE_MAPPINGS.get(field.type, {}).get("cpp", "std::string")
        if field.optional:
            return f"std::optional<{base}>"
        return base
    
    def _generate_tojson_field(self, field: PacketField) -> list:
        """Generate ToJson code for a single field, handling optional properly."""
        lines = []
        field_access = f"{field.name}_"
        value_access = f"{field.name}_.value()" if field.optional else field_access
        
        if field.optional:
            lines.append(f"{self._i()}if ({field_access}.has_value()) {{")
            indent = self._i(2)
        else:
            indent = self._i()
        
        if field.type in ['int', 'bigint']:
            lines.append(f'{indent}yyjson_mut_obj_add_int(doc, root, "{field.name}", {value_access});')
        elif field.type in ['float', 'double']:
            lines.append(f'{indent}yyjson_mut_obj_add_real(doc, root, "{field.name}", {value_access});')
        elif field.type == 'bool':
            lines.append(f'{indent}yyjson_mut_obj_add_bool(doc, root, "{field.name}", {value_access});')
        elif field.type in ['string', 'datetime', 'time']:
            lines.append(f'{indent}yyjson_mut_obj_add_strcpy(doc, root, "{field.name}", {value_access}.c_str());')
        elif field.type == 'bytes':
            # Encode bytes as base64
            lines.append(f"{indent}{{")
            lines.append(f"{indent}{self._i()}std::string encoded;")
            lines.append(f"{indent}{self._i()}static const char* chars = \"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/\";")
            lines.append(f"{indent}{self._i()}const auto& bytes = {value_access};")
            lines.append(f"{indent}{self._i()}size_t len = bytes.size();")
            lines.append(f"{indent}{self._i()}for (size_t i = 0; i < len; i += 3) {{")
            lines.append(f"{indent}{self._i(2)}uint32_t octet_a = bytes[i];")
            lines.append(f"{indent}{self._i(2)}uint32_t octet_b = (i + 1 < len) ? bytes[i + 1] : 0;")
            lines.append(f"{indent}{self._i(2)}uint32_t octet_c = (i + 2 < len) ? bytes[i + 2] : 0;")
            lines.append(f"{indent}{self._i(2)}uint32_t triple = (octet_a << 16) | (octet_b << 8) | octet_c;")
            lines.append(f"{indent}{self._i(2)}encoded += chars[(triple >> 18) & 0x3F];")
            lines.append(f"{indent}{self._i(2)}encoded += chars[(triple >> 12) & 0x3F];")
            lines.append(f"{indent}{self._i(2)}encoded += (i + 1 < len) ? chars[(triple >> 6) & 0x3F] : '=';")
            lines.append(f"{indent}{self._i(2)}encoded += (i + 2 < len) ? chars[triple & 0x3F] : '=';")
            lines.append(f"{indent}{self._i()}}}")
            lines.append(f'{indent}{self._i()}yyjson_mut_obj_add_strcpy(doc, root, "{field.name}", encoded.c_str());')
            lines.append(f"{indent}}}")
        elif field.type == 'list_int':
            lines.append(f"{indent}{{")
            lines.append(f"{indent}{self._i()}yyjson_mut_val* arr = yyjson_mut_arr(doc);")
            lines.append(f"{indent}{self._i()}for (const auto& item : {value_access}) {{")
            lines.append(f"{indent}{self._i(2)}yyjson_mut_arr_add_int(doc, arr, item);")
            lines.append(f"{indent}{self._i()}}}")
            lines.append(f'{indent}{self._i()}yyjson_mut_obj_add_val(doc, root, "{field.name}", arr);')
            lines.append(f"{indent}}}")
        elif field.type == 'list_string':
            lines.append(f"{indent}{{")
            lines.append(f"{indent}{self._i()}yyjson_mut_val* arr = yyjson_mut_arr(doc);")
            lines.append(f"{indent}{self._i()}for (const auto& item : {value_access}) {{")
            lines.append(f"{indent}{self._i(2)}yyjson_mut_arr_add_strcpy(doc, arr, item.c_str());")
            lines.append(f"{indent}{self._i()}}}")
            lines.append(f'{indent}{self._i()}yyjson_mut_obj_add_val(doc, root, "{field.name}", arr);')
            lines.append(f"{indent}}}")
        elif field.type in ['list', 'map', 'map_string_dynamic', 'embedded_map']:
            lines.append(f"{indent}{{")
            lines.append(f"{indent}{self._i()}yyjson_doc* sub_doc = yyjson_read({value_access}.c_str(), {value_access}.size(), 0);")
            lines.append(f"{indent}{self._i()}if (sub_doc) {{")
            lines.append(f"{indent}{self._i(2)}yyjson_val* sub_root = yyjson_doc_get_root(sub_doc);")
            lines.append(f"{indent}{self._i(2)}yyjson_mut_val* copied = yyjson_val_mut_copy(doc, sub_root);")
            lines.append(f'{indent}{self._i(2)}yyjson_mut_obj_add_val(doc, root, "{field.name}", copied);')
            lines.append(f"{indent}{self._i(2)}yyjson_doc_free(sub_doc);")
            lines.append(f"{indent}{self._i()}}} else {{")
            lines.append(f'{indent}{self._i(2)}yyjson_mut_obj_add_null(doc, root, "{field.name}");')
            lines.append(f"{indent}{self._i()}}}")
            lines.append(f"{indent}}}")
        else:
            lines.append(f'{indent}yyjson_mut_obj_add_strcpy(doc, root, "{field.name}", {value_access}.c_str());')
        
        if field.optional:
            lines.append(f"{self._i()}}} else {{")
            lines.append(f'{self._i(2)}yyjson_mut_obj_add_null(doc, root, "{field.name}");')
            lines.append(f"{self._i()}}}")
        
        return lines
    
    def _generate_fromjson_field(self, field: PacketField) -> list:
        """Generate FromJson code for a single field, handling optional properly."""
        lines = []
        lines.append(f'{self._i()}yyjson_val* {field.name}_val = yyjson_obj_get(root, "{field.name}");')
        
        if field.type in ['int', 'bigint']:
            lines.append(f"{self._i()}if ({field.name}_val && yyjson_is_int({field.name}_val)) {{")
            lines.append(f"{self._i(2)}packet.{field.name}_ = yyjson_get_sint({field.name}_val);")
            lines.append(f"{self._i()}}}")
        elif field.type in ['float', 'double']:
            lines.append(f"{self._i()}if ({field.name}_val && (yyjson_is_real({field.name}_val) || yyjson_is_int({field.name}_val))) {{")
            lines.append(f"{self._i(2)}packet.{field.name}_ = yyjson_get_num({field.name}_val);")
            lines.append(f"{self._i()}}}")
        elif field.type == 'bool':
            lines.append(f"{self._i()}if ({field.name}_val && yyjson_is_bool({field.name}_val)) {{")
            lines.append(f"{self._i(2)}packet.{field.name}_ = yyjson_get_bool({field.name}_val);")
            lines.append(f"{self._i()}}}")
        elif field.type in ['string', 'datetime', 'time']:
            lines.append(f"{self._i()}if ({field.name}_val && yyjson_is_str({field.name}_val)) {{")
            lines.append(f"{self._i(2)}packet.{field.name}_ = yyjson_get_str({field.name}_val);")
            lines.append(f"{self._i()}}}")
        elif field.type == 'bytes':
            # Decode base64 to bytes - with null safety
            lines.append(f"{self._i()}if ({field.name}_val && yyjson_is_str({field.name}_val)) {{")
            lines.append(f"{self._i(2)}const char* encoded = yyjson_get_str({field.name}_val);")
            lines.append(f"{self._i(2)}if (encoded && *encoded) {{")
            lines.append(f"{self._i(3)}std::vector<unsigned char> decoded;")
            lines.append(f"{self._i(3)}static const int decode_table[256] = {{")
            lines.append(f"{self._i(4)}-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,")
            lines.append(f"{self._i(4)}-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,62,-1,-1,-1,63,52,53,54,55,56,57,58,59,60,61,-1,-1,-1,-1,-1,-1,")
            lines.append(f"{self._i(4)}-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,-1,-1,-1,-1,-1,")
            lines.append(f"{self._i(4)}-1,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,-1,-1,-1,-1,-1")
            lines.append(f"{self._i(3)}}};")
            lines.append(f"{self._i(3)}size_t len = strlen(encoded);")
            lines.append(f"{self._i(3)}for (size_t i = 0; i < len; i += 4) {{")
            lines.append(f"{self._i(4)}int a = decode_table[(unsigned char)encoded[i]];")
            lines.append(f"{self._i(4)}int b = (i+1 < len) ? decode_table[(unsigned char)encoded[i+1]] : 0;")
            lines.append(f"{self._i(4)}int c = (i+2 < len && encoded[i+2] != '=') ? decode_table[(unsigned char)encoded[i+2]] : 0;")
            lines.append(f"{self._i(4)}int d = (i+3 < len && encoded[i+3] != '=') ? decode_table[(unsigned char)encoded[i+3]] : 0;")
            lines.append(f"{self._i(4)}decoded.push_back((a << 2) | (b >> 4));")
            lines.append(f"{self._i(4)}if (i+2 < len && encoded[i+2] != '=') decoded.push_back(((b & 0xF) << 4) | (c >> 2));")
            lines.append(f"{self._i(4)}if (i+3 < len && encoded[i+3] != '=') decoded.push_back(((c & 0x3) << 6) | d);")
            lines.append(f"{self._i(3)}}}")
            lines.append(f"{self._i(3)}packet.{field.name}_ = decoded;")
            lines.append(f"{self._i(2)}}}")
            lines.append(f"{self._i()}}}")
        elif field.type == 'list_int':
            lines.append(f"{self._i()}if ({field.name}_val && yyjson_is_arr({field.name}_val)) {{")
            if field.optional:
                lines.append(f"{self._i(2)}std::vector<int64_t> items;")
            lines.append(f"{self._i(2)}size_t idx, max;")
            lines.append(f"{self._i(2)}yyjson_val* item;")
            lines.append(f"{self._i(2)}yyjson_arr_foreach({field.name}_val, idx, max, item) {{")
            lines.append(f"{self._i(3)}if (yyjson_is_int(item)) {{")
            if field.optional:
                lines.append(f"{self._i(4)}items.push_back(yyjson_get_sint(item));")
            else:
                lines.append(f"{self._i(4)}packet.{field.name}_.push_back(yyjson_get_sint(item));")
            lines.append(f"{self._i(3)}}}")
            lines.append(f"{self._i(2)}}}")
            if field.optional:
                lines.append(f"{self._i(2)}packet.{field.name}_ = items;")
            lines.append(f"{self._i()}}}")
        elif field.type == 'list_string':
            lines.append(f"{self._i()}if ({field.name}_val && yyjson_is_arr({field.name}_val)) {{")
            if field.optional:
                lines.append(f"{self._i(2)}std::vector<std::string> items;")
            lines.append(f"{self._i(2)}size_t idx, max;")
            lines.append(f"{self._i(2)}yyjson_val* item;")
            lines.append(f"{self._i(2)}yyjson_arr_foreach({field.name}_val, idx, max, item) {{")
            lines.append(f"{self._i(3)}if (yyjson_is_str(item)) {{")
            if field.optional:
                lines.append(f"{self._i(4)}items.push_back(yyjson_get_str(item));")
            else:
                lines.append(f"{self._i(4)}packet.{field.name}_.push_back(yyjson_get_str(item));")
            lines.append(f"{self._i(3)}}}")
            lines.append(f"{self._i(2)}}}")
            if field.optional:
                lines.append(f"{self._i(2)}packet.{field.name}_ = items;")
            lines.append(f"{self._i()}}}")
        elif field.type in ['list', 'map', 'map_string_dynamic', 'embedded_map']:
            lines.append(f"{self._i()}if ({field.name}_val) {{")
            lines.append(f"{self._i(2)}char* sub_json = yyjson_val_write({field.name}_val, 0, nullptr);")
            lines.append(f"{self._i(2)}if (sub_json) {{")
            lines.append(f"{self._i(3)}packet.{field.name}_ = sub_json;")
            lines.append(f"{self._i(3)}free(sub_json);")
            lines.append(f"{self._i(2)}}}")
            lines.append(f"{self._i()}}}")
        else:
            lines.append(f"{self._i()}if ({field.name}_val && yyjson_is_str({field.name}_val)) {{")
            lines.append(f"{self._i(2)}packet.{field.name}_ = yyjson_get_str({field.name}_val);")
            lines.append(f"{self._i()}}}")
        
        return lines
    
    def generate_packet(self, packet: PacketDefinition) -> tuple:
        """Generate C++ header and source code for a packet."""
        header_lines = []
        source_lines = []
        
        # Header file
        header_lines.append("// Auto-generated by CrossPacket - do not modify manually")
        header_lines.append("#pragma once")
        header_lines.append("")
        header_lines.append("#include <string>")
        header_lines.append("#include <vector>")
        header_lines.append("#include <optional>")
        header_lines.append("#include <cstdint>")
        header_lines.append("#include <cstring>")
        header_lines.append("#include <stdexcept>")
        if not self.no_json:
            header_lines.append("#include <yyjson.h>")
        if not self.no_msgpack:
            header_lines.append("#include <msgpack.hpp>")
        header_lines.append("")
        header_lines.append(f"namespace {self.namespace} {{")
        header_lines.append("")
        
        # Class documentation
        if packet.description:
            header_lines.append(f"/// @brief {packet.description}")
        
        header_lines.append(f"class {packet.name} {{")
        header_lines.append("public:")
        
        # Type constant
        header_lines.append(f'{self._i()}static constexpr const char* TYPE = "{packet.path}";')
        header_lines.append("")
        
        # Default constructor
        header_lines.append(f"{self._i()}{packet.name}() = default;")
        
        # Parameterized constructor
        if packet.fields:
            params = []
            for field in packet.fields:
                cpp_type = self.cpp_type(field)
                if cpp_type.startswith("std::"):
                    params.append(f"const {cpp_type}& {field.name}")
                else:
                    params.append(f"{cpp_type} {field.name}")
            header_lines.append(f"{self._i()}{packet.name}({', '.join(params)});")
        header_lines.append("")
        
        # Getters
        for field in packet.fields:
            cpp_type = self.cpp_type(field)
            pascal_name = to_pascal_case(field.name)
            if cpp_type.startswith("std::"):
                header_lines.append(f"{self._i()}const {cpp_type}& Get{pascal_name}() const {{ return {field.name}_; }}")
            else:
                header_lines.append(f"{self._i()}{cpp_type} Get{pascal_name}() const {{ return {field.name}_; }}")
        header_lines.append("")
        
        # Setters
        for field in packet.fields:
            cpp_type = self.cpp_type(field)
            pascal_name = to_pascal_case(field.name)
            if cpp_type.startswith("std::"):
                header_lines.append(f"{self._i()}void Set{pascal_name}(const {cpp_type}& value) {{ {field.name}_ = value; }}")
            else:
                header_lines.append(f"{self._i()}void Set{pascal_name}({cpp_type} value) {{ {field.name}_ = value; }}")
        header_lines.append("")
        
        # Serialization methods
        if not self.no_json:
            header_lines.append(f"{self._i()}std::string ToJson() const;")
            header_lines.append(f"{self._i()}static {packet.name} FromJson(const std::string& json);")
        
        if not self.no_msgpack:
            header_lines.append(f"{self._i()}std::vector<uint8_t> ToMsgPack() const;")
            header_lines.append(f"{self._i()}static {packet.name} FromMsgPack(const std::vector<uint8_t>& data);")
            header_lines.append("")
            header_lines.append(f"{self._i()}MSGPACK_DEFINE_MAP(type_, {', '.join(f'{f.name}_' for f in packet.fields)});")
        
        header_lines.append("")
        header_lines.append("private:")
        header_lines.append(f'{self._i()}std::string type_ = "{packet.path}";')
        for field in packet.fields:
            cpp_type = self.cpp_type(field)
            header_lines.append(f"{self._i()}{cpp_type} {field.name}_;")
        
        header_lines.append("};")
        header_lines.append("")
        header_lines.append(f"}} // namespace {self.namespace}")
        
        # Source file
        source_lines.append("// Auto-generated by CrossPacket - do not modify manually")
        source_lines.append(f'#include "{to_snake_case(packet.name)}.hpp"')
        if not self.no_json:
            source_lines.append("#include <cstdlib>")
        source_lines.append("")
        source_lines.append(f"namespace {self.namespace} {{")
        source_lines.append("")
        
        # Constructor implementation
        if packet.fields:
            params = []
            for field in packet.fields:
                cpp_type = self.cpp_type(field)
                if cpp_type.startswith("std::"):
                    params.append(f"const {cpp_type}& {field.name}")
                else:
                    params.append(f"{cpp_type} {field.name}")
            source_lines.append(f"{packet.name}::{packet.name}({', '.join(params)})")
            init_list = [f"{field.name}_({field.name})" for field in packet.fields]
            source_lines.append(f"{self._i()}: {', '.join(init_list)} {{}}")
            source_lines.append("")
        
        # JSON methods using yyjson
        if not self.no_json:
            # ToJson implementation
            source_lines.append(f"std::string {packet.name}::ToJson() const {{")
            source_lines.append(f"{self._i()}yyjson_mut_doc* doc = yyjson_mut_doc_new(nullptr);")
            source_lines.append(f"{self._i()}yyjson_mut_val* root = yyjson_mut_obj(doc);")
            source_lines.append(f"{self._i()}yyjson_mut_doc_set_root(doc, root);")
            source_lines.append("")
            source_lines.append(f'{self._i()}yyjson_mut_obj_add_str(doc, root, "{self.type_field}", TYPE);')
            
            for field in packet.fields:
                source_lines.extend(self._generate_tojson_field(field))
            
            source_lines.append("")
            source_lines.append(f"{self._i()}char* json = yyjson_mut_write(doc, 0, nullptr);")
            source_lines.append(f"{self._i()}std::string result(json);")
            source_lines.append(f"{self._i()}free(json);")
            source_lines.append(f"{self._i()}yyjson_mut_doc_free(doc);")
            source_lines.append(f"{self._i()}return result;")
            source_lines.append("}")
            source_lines.append("")
            
            # FromJson implementation
            source_lines.append(f"{packet.name} {packet.name}::FromJson(const std::string& json) {{")
            source_lines.append(f"{self._i()}yyjson_doc* doc = yyjson_read(json.c_str(), json.size(), 0);")
            source_lines.append(f"{self._i()}if (!doc) {{")
            source_lines.append(f'{self._i(2)}throw std::runtime_error("JSON parse error");')
            source_lines.append(f"{self._i()}}}")
            source_lines.append("")
            source_lines.append(f"{self._i()}yyjson_val* root = yyjson_doc_get_root(doc);")
            source_lines.append(f"{self._i()}{packet.name} packet;")
            source_lines.append("")
            
            for field in packet.fields:
                source_lines.extend(self._generate_fromjson_field(field))
            
            source_lines.append("")
            source_lines.append(f"{self._i()}yyjson_doc_free(doc);")
            source_lines.append(f"{self._i()}return packet;")
            source_lines.append("}")
            source_lines.append("")
        
        # MsgPack methods
        if not self.no_msgpack:
            source_lines.append(f"std::vector<uint8_t> {packet.name}::ToMsgPack() const {{")
            source_lines.append(f"{self._i()}msgpack::sbuffer buffer;")
            source_lines.append(f"{self._i()}msgpack::pack(buffer, *this);")
            source_lines.append(f"{self._i()}return std::vector<uint8_t>(buffer.data(), buffer.data() + buffer.size());")
            source_lines.append("}")
            source_lines.append("")
            
            source_lines.append(f"{packet.name} {packet.name}::FromMsgPack(const std::vector<uint8_t>& data) {{")
            source_lines.append(f"{self._i()}msgpack::object_handle oh = msgpack::unpack(reinterpret_cast<const char*>(data.data()), data.size());")
            source_lines.append(f"{self._i()}return oh.get().as<{packet.name}>();")
            source_lines.append("}")
        
        source_lines.append("")
        source_lines.append(f"}} // namespace {self.namespace}")
        
        return "\n".join(header_lines), "\n".join(source_lines)
    
    def generate(self, packets: List[PacketDefinition], override: bool = False, clean: bool = False, no_msgpack: bool = False, no_json: bool = False, type_field: str = "packetType"):
        """Generate all C++ files."""
        self.type_field = type_field
        self.no_msgpack = no_msgpack
        self.no_json = no_json
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if clean:
            for f in self.output_dir.glob("*.hpp"):
                f.unlink()
            for f in self.output_dir.glob("*.cpp"):
                f.unlink()
        
        if no_msgpack:
            print("MessagePack support disabled - generating JSON-only code")
        elif no_json:
            print("JSON support disabled - generating MessagePack-only code")
        
        # Generate config header with feature flags
        config_path = self.output_dir / "crosspacket_config.hpp"
        config_code = self._generate_config_header(no_msgpack, no_json)
        config_path.write_text(config_code)
        print(f"Generated: {config_path}")
        
        for packet in packets:
            header_path = self.output_dir / f"{to_snake_case(packet.name)}.hpp"
            source_path = self.output_dir / f"{to_snake_case(packet.name)}.cpp"
            
            if not header_path.exists() or override:
                header_code, source_code = self.generate_packet(packet)
                header_path.write_text(header_code)
                source_path.write_text(source_code)
                print(f"Generated: {header_path}")
                print(f"Generated: {source_path}")
            else:
                print(f"Skipped (exists): {header_path}")
    
    def _generate_config_header(self, no_msgpack: bool, no_json: bool) -> str:
        """Generate crosspacket_config.hpp with feature flags."""
        lines = []
        lines.append("// Auto-generated by CrossPacket - do not modify manually")
        lines.append("// Configuration header defining enabled serialization features")
        lines.append("#pragma once")
        lines.append("")
        lines.append("// Serialization feature flags")
        if not no_json:
            lines.append("#define CROSSPACKET_HAS_JSON 1")
        else:
            lines.append("// #define CROSSPACKET_HAS_JSON 0  // JSON disabled")
        if not no_msgpack:
            lines.append("#define CROSSPACKET_HAS_MSGPACK 1")
        else:
            lines.append("// #define CROSSPACKET_HAS_MSGPACK 0  // MessagePack disabled")
        lines.append("")
        return "\n".join(lines)


class CSharpGenerator:
    """Generates C# packet code with System.Text.Json and MessagePack-CSharp support."""
    
    def __init__(self, config: Dict[str, Any]):
        self.output_dir = Path(config.get("output_dir", "./generated/csharp"))
        self.namespace = config.get("namespace", "CrossPacket")
        self.indent = config.get("indent", "    ")
    
    def _i(self, level: int = 1) -> str:
        """Return indentation for the given level."""
        return self.indent * level
    
    def csharp_type(self, field: PacketField) -> str:
        """Get C# type for a field."""
        base = TYPE_MAPPINGS.get(field.type, {}).get("csharp", "object")
        if field.optional:
            return f"{base}?"
        return base
    
    def generate_packet(self, packet: PacketDefinition) -> str:
        """Generate C# code for a packet."""
        lines = []
        
        lines.append("// Auto-generated by CrossPacket - do not modify manually")
        lines.append("using System;")
        lines.append("using System.Collections.Generic;")
        if not self.no_json:
            lines.append("using System.Text.Json;")
            lines.append("using System.Text.Json.Serialization;")
        if not self.no_msgpack:
            lines.append("using MessagePack;")
        lines.append("")
        lines.append(f"namespace {self.namespace}")
        lines.append("{")
        
        # Class documentation
        if packet.description:
            lines.append(f"{self._i()}/// <summary>")
            lines.append(f"{self._i()}/// {packet.description}")
            lines.append(f"{self._i()}/// </summary>")
        
        # MessagePack attribute
        if not self.no_msgpack:
            lines.append(f"{self._i()}[MessagePackObject]")
        
        lines.append(f"{self._i()}public class {packet.name}")
        lines.append(f"{self._i()}{{")
        
        # Type constant
        lines.append(f'{self._i(2)}public const string TYPE = "{packet.path}";')
        lines.append("")
        
        # Type property
        if not self.no_msgpack:
            lines.append(f'{self._i(2)}[Key(\"{self.type_field}\")]')
        if not self.no_json:
            lines.append(f'{self._i(2)}[JsonPropertyName(\"{self.type_field}\")]')
        lines.append(f'{self._i(2)}public string Type {{ get; set; }} = TYPE;')
        lines.append("")
        
        # Properties
        key_index = 1
        for field in packet.fields:
            csharp_type = self.csharp_type(field)
            pascal_name = to_pascal_case(field.name)
            
            if field.description:
                lines.append(f"{self._i(2)}/// <summary>{field.description}</summary>")
            
            if not self.no_msgpack:
                lines.append(f'{self._i(2)}[Key("{field.name}")]')
            if not self.no_json:
                lines.append(f'{self._i(2)}[JsonPropertyName("{field.name}")]')
            
            default = self._get_csharp_default(field.type, field.optional)
            lines.append(f"{self._i(2)}public {csharp_type} {pascal_name} {{ get; set; }}{default}")
            lines.append("")
            key_index += 1
        
        # Default constructor
        lines.append(f"{self._i(2)}public {packet.name}() {{ }}")
        lines.append("")
        
        # Parameterized constructor
        if packet.fields:
            params = []
            for field in packet.fields:
                csharp_type = self.csharp_type(field)
                param_name = to_camel_case(field.name)
                params.append(f"{csharp_type} {param_name}")
            lines.append(f"{self._i(2)}public {packet.name}({', '.join(params)})")
            lines.append(f"{self._i(2)}{{")
            for field in packet.fields:
                pascal_name = to_pascal_case(field.name)
                param_name = to_camel_case(field.name)
                lines.append(f"{self._i(3)}this.{pascal_name} = {param_name};")
            lines.append(f"{self._i(2)}}}")
            lines.append("")
        
        # JSON methods
        if not self.no_json:
            lines.append(f"{self._i(2)}public string ToJson()")
            lines.append(f"{self._i(2)}{{")
            lines.append(f"{self._i(3)}return JsonSerializer.Serialize(this);")
            lines.append(f"{self._i(2)}}}")
            lines.append("")
            
            lines.append(f"{self._i(2)}public static {packet.name}? FromJson(string json)")
            lines.append(f"{self._i(2)}{{")
            lines.append(f"{self._i(3)}return JsonSerializer.Deserialize<{packet.name}>(json);")
            lines.append(f"{self._i(2)}}}")
            lines.append("")
        
        # MsgPack methods
        if not self.no_msgpack:
            lines.append(f"{self._i(2)}public byte[] ToMsgPack()")
            lines.append(f"{self._i(2)}{{")
            lines.append(f"{self._i(3)}return MessagePackSerializer.Serialize(this);")
            lines.append(f"{self._i(2)}}}")
            lines.append("")
            
            lines.append(f"{self._i(2)}public static {packet.name} FromMsgPack(byte[] data)")
            lines.append(f"{self._i(2)}{{")
            lines.append(f"{self._i(3)}return MessagePackSerializer.Deserialize<{packet.name}>(data);")
            lines.append(f"{self._i(2)}}}")
        
        lines.append(f"{self._i()}}}")
        lines.append("}")
        
        return "\n".join(lines)
    
    def _get_csharp_default(self, field_type: str, optional: bool) -> str:
        """Get default value for C# field."""
        if optional:
            return ""
        if field_type == "string":
            return ' = "";'
        if field_type == "bytes":
            return " = Array.Empty<byte>();"
        if field_type in ["list", "list_int", "list_string"]:
            base = TYPE_MAPPINGS.get(field_type, {}).get("csharp", "List<object>")
            return f" = new {base}();"
        if field_type in ["map", "embedded_map", "map_string_dynamic"]:
            base = TYPE_MAPPINGS.get(field_type, {}).get("csharp", "Dictionary<string, object>")
            return f" = new {base}();"
        return ""
    
    def generate(self, packets: List[PacketDefinition], override: bool = False, clean: bool = False, no_msgpack: bool = False, no_json: bool = False, type_field: str = "packetType"):
        """Generate all C# files."""
        self.type_field = type_field
        self.no_msgpack = no_msgpack
        self.no_json = no_json
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if clean:
            for f in self.output_dir.glob("*.cs"):
                f.unlink()
        
        if no_msgpack:
            print("MessagePack support disabled - generating JSON-only code")
        elif no_json:
            print("JSON support disabled - generating MessagePack-only code")
        
        for packet in packets:
            filename = f"{packet.name}.cs"
            filepath = self.output_dir / filename
            if not filepath.exists() or override:
                filepath.write_text(self.generate_packet(packet))
                print(f"Generated: {filepath}")
            else:
                print(f"Skipped (exists): {filepath}")


class PhpGenerator:
    """Generates PHP packet code with json and msgpack extension support."""
    
    def __init__(self, config: Dict[str, Any]):
        self.output_dir = Path(config.get("output_dir", "./generated/php"))
        self.namespace = config.get("namespace", "CrossPacket")
        self.indent = config.get("indent", "    ")
    
    def _i(self, level: int = 1) -> str:
        """Return indentation for the given level."""
        return self.indent * level
    
    def php_type(self, field: PacketField) -> str:
        """Get PHP type for a field."""
        base = TYPE_MAPPINGS.get(field.type, {}).get("php", "mixed")
        # mixed already includes null, so don't add ? prefix
        if base == "mixed":
            return "mixed"
        if field.optional:
            return f"?{base}"
        return base
    
    def php_nullable_type(self, field: PacketField) -> str:
        """Get PHP nullable type for a field property."""
        base = TYPE_MAPPINGS.get(field.type, {}).get("php", "mixed")
        # mixed already includes null
        if base == "mixed":
            return "mixed"
        return f"?{base}"
    
    def generate_packet(self, packet: PacketDefinition) -> str:
        """Generate PHP code for a packet."""
        lines = []
        
        lines.append("<?php")
        lines.append("// Auto-generated by CrossPacket - do not modify manually")
        lines.append("")
        lines.append("declare(strict_types=1);")
        lines.append("")
        lines.append(f"namespace {self.namespace};")
        lines.append("")
        lines.append("use DateTimeImmutable;")
        lines.append("use DateTimeInterface;")
        if not self.no_json:
            lines.append("use JsonSerializable;")
        lines.append("")
        
        # Class documentation
        if packet.description:
            lines.append("/**")
            lines.append(f" * {packet.description}")
            lines.append(" */")
        
        if not self.no_json:
            lines.append(f"class {packet.name} implements JsonSerializable")
        else:
            lines.append(f"class {packet.name}")
        lines.append("{")
        
        # Type constant
        lines.append(f"{self._i()}public const TYPE = '{packet.path}';")
        lines.append("")
        
        # Properties with nullable types for flexibility
        for field in packet.fields:
            nullable_type = self.php_nullable_type(field)
            if field.description:
                lines.append(f"{self._i()}/** @var {nullable_type} {field.description} */")
            lines.append(f"{self._i()}private {nullable_type} ${field.name} = null;")
        lines.append("")
        
        # Default constructor (no parameters required - use setters)
        lines.append(f"{self._i()}public function __construct(")
        if packet.fields:
            params = []
            for field in packet.fields:
                php_type = self.php_nullable_type(field)
                params.append(f"{php_type} ${field.name} = null")
            lines.append(f"{self._i(2)}" + f",\n{self._i(2)}".join(params))
        lines.append(f"{self._i()})")
        lines.append(f"{self._i()}{{")
        for field in packet.fields:
            lines.append(f"{self._i(2)}$this->{field.name} = ${field.name};")
        lines.append(f"{self._i()}}}")
        lines.append("")
        
        # Getters and Setters
        for field in packet.fields:
            php_type = self.php_type(field)
            nullable_type = self.php_nullable_type(field)
            pascal_name = to_pascal_case(field.name)
            
            # Getter (returns nullable)
            lines.append(f"{self._i()}public function get{pascal_name}(): {nullable_type}")
            lines.append(f"{self._i()}{{")
            lines.append(f"{self._i(2)}return $this->{field.name};")
            lines.append(f"{self._i()}}}")
            lines.append("")
            
            # Setter (accepts the proper type)
            lines.append(f"{self._i()}public function set{pascal_name}({php_type} ${field.name}): self")
            lines.append(f"{self._i()}{{")
            lines.append(f"{self._i(2)}$this->{field.name} = ${field.name};")
            lines.append(f"{self._i(2)}return $this;")
            lines.append(f"{self._i()}}}")
            lines.append("")
        
        # jsonSerialize method
        if not self.no_json:
            lines.append(f"{self._i()}public function jsonSerialize(): array")
            lines.append(f"{self._i()}{{")
            lines.append(f"{self._i(2)}return [")
            lines.append(f"{self._i(3)}'{self.type_field}' => self::TYPE,")
            for field in packet.fields:
                encode = self._php_encode(field.name, field.type)
                lines.append(f"{self._i(3)}'{field.name}' => {encode},")
            lines.append(f"{self._i(2)}];")
            lines.append(f"{self._i()}}}")
            lines.append("")
            
            # toJson method
            lines.append(f"{self._i()}public function toJson(): string")
            lines.append(f"{self._i()}{{")
            lines.append(f"{self._i(2)}return json_encode($this->jsonSerialize(), JSON_THROW_ON_ERROR);")
            lines.append(f"{self._i()}}}")
            lines.append("")
            
            # fromJson static method - use setters
            lines.append(f"{self._i()}public static function fromJson(string $json): self")
            lines.append(f"{self._i()}{{")
            lines.append(f"{self._i(2)}$data = json_decode($json, true, 512, JSON_THROW_ON_ERROR);")
            lines.append(f"{self._i(2)}$instance = new self();")
            for field in packet.fields:
                pascal_name = to_pascal_case(field.name)
                decode = self._php_decode_value(field.name, field.type, "$data")
                lines.append(f"{self._i(2)}if (isset($data['{field.name}'])) {{")
                lines.append(f"{self._i(3)}$instance->set{pascal_name}({decode});")
                lines.append(f"{self._i(2)}}}")
            lines.append(f"{self._i(2)}return $instance;")
            lines.append(f"{self._i()}}}")
            lines.append("")
        
        # MsgPack methods
        if not self.no_msgpack:
            # Helper method for packing if jsonSerialize is not available
            if self.no_json:
                lines.append(f"{self._i()}private function toArray(): array")
                lines.append(f"{self._i()}{{")
                lines.append(f"{self._i(2)}return [")
                lines.append(f"{self._i(3)}'{self.type_field}' => self::TYPE,")
                for field in packet.fields:
                    encode = self._php_encode(field.name, field.type)
                    lines.append(f"{self._i(3)}'{field.name}' => {encode},")
                lines.append(f"{self._i(2)}];")
                lines.append(f"{self._i()}}}")
                lines.append("")
            
            lines.append(f"{self._i()}public function toMsgPack(): string")
            lines.append(f"{self._i()}{{")
            if self.no_json:
                lines.append(f"{self._i(2)}return msgpack_pack($this->toArray());")
            else:
                lines.append(f"{self._i(2)}return msgpack_pack($this->jsonSerialize());")
            lines.append(f"{self._i()}}}")
            lines.append("")
            
            # fromMsgPack - use setters
            lines.append(f"{self._i()}public static function fromMsgPack(string $data): self")
            lines.append(f"{self._i()}{{")
            lines.append(f"{self._i(2)}$arr = msgpack_unpack($data);")
            lines.append(f"{self._i(2)}$instance = new self();")
            for field in packet.fields:
                pascal_name = to_pascal_case(field.name)
                decode = self._php_decode_value(field.name, field.type, "$arr")
                lines.append(f"{self._i(2)}if (isset($arr['{field.name}'])) {{")
                lines.append(f"{self._i(3)}$instance->set{pascal_name}({decode});")
                lines.append(f"{self._i(2)}}}")
            lines.append(f"{self._i(2)}return $instance;")
            lines.append(f"{self._i()}}}")
        
        lines.append("}")
        
        return "\n".join(lines)
    
    def _php_encode(self, field_name: str, field_type: str) -> str:
        """Get PHP encoding expression for a field."""
        if field_type == "datetime":
            return f"$this->{field_name}?->format(\\DateTimeInterface::ATOM)"
        return f"$this->{field_name}"
    
    def _php_decode_value(self, field_name: str, field_type: str, source: str) -> str:
        """Get PHP decoding expression for a field value."""
        if field_type == "datetime":
            return f"new \\DateTimeImmutable({source}['{field_name}'])"
        return f"{source}['{field_name}']"
    
    def _php_decode(self, field_name: str, field_type: str) -> str:
        """Get PHP decoding expression for a field from JSON data."""
        if field_type == "datetime":
            return f"isset($data['{field_name}']) ? new \\DateTimeImmutable($data['{field_name}']) : null"
        return f"$data['{field_name}'] ?? null"
    
    def _php_decode_array(self, field_name: str, field_type: str) -> str:
        """Get PHP decoding expression for a field from msgpack array."""
        if field_type == "datetime":
            return f"isset($arr['{field_name}']) ? new \\DateTimeImmutable($arr['{field_name}']) : null"
        return f"$arr['{field_name}'] ?? null"
    
    def generate(self, packets: List[PacketDefinition], override: bool = False, clean: bool = False, no_msgpack: bool = False, no_json: bool = False, type_field: str = "packetType"):
        """Generate all PHP files."""
        self.type_field = type_field
        self.no_msgpack = no_msgpack
        self.no_json = no_json
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if clean:
            for f in self.output_dir.glob("*.php"):
                f.unlink()
        
        if no_msgpack:
            print("MessagePack support disabled - generating JSON-only code")
        elif no_json:
            print("JSON support disabled - generating MessagePack-only code")
        
        for packet in packets:
            filename = f"{packet.name}.php"
            filepath = self.output_dir / filename
            if not filepath.exists() or override:
                filepath.write_text(self.generate_packet(packet))
                print(f"Generated: {filepath}")
            else:
                print(f"Skipped (exists): {filepath}")


def load_config(config_path: str) -> Dict[str, Any]:
    """Load and parse the packets.json configuration file."""
    path = Path(config_path)
    if not path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="CrossPacket - Cross-platform data packet generator (JSON + MessagePack)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py --dart                    Generate Dart code only
  python generate.py --python                  Generate Python code only
  python generate.py --all --override          Generate all platforms, overwrite existing
  python generate.py --config my_packets.json  Use custom config file
        """
    )
    
    parser.add_argument("--config", default="./packets.json",
                        help="Path to packets.json config file (default: ./packets.json)")
    parser.add_argument("--dart", action="store_true", help="Generate Dart code")
    parser.add_argument("--python", action="store_true", help="Generate Python code")
    parser.add_argument("--java", action="store_true", help="Generate Java code")
    parser.add_argument("--typescript", action="store_true", help="Generate TypeScript code")
    parser.add_argument("--rust", action="store_true", help="Generate Rust code")
    parser.add_argument("--go", action="store_true", help="Generate Go code")
    parser.add_argument("--cpp", action="store_true", help="Generate C++ code")
    parser.add_argument("--csharp", action="store_true", help="Generate C# code")
    parser.add_argument("--php", action="store_true", help="Generate PHP code")
    parser.add_argument("--all", action="store_true", help="Generate all platforms")
    parser.add_argument("--override", action="store_true", help="Override existing files")
    parser.add_argument("--clean", action="store_true", help="Remove old generated files first")
    parser.add_argument("--no-msgpack", action="store_true", dest="no_msgpack",
                        help="Generate JSON-only code without MessagePack dependency")
    parser.add_argument("--no-json", action="store_true", dest="no_json",
                        help="Generate MessagePack-only code without JSON serialization")
    parser.add_argument("--strict", action="store_true",
                        help="Generate with strict validation (required field checks, bounds validation)")
    parser.add_argument("--max-list-size", type=int, default=100000, dest="max_list_size",
                        help="Maximum allowed list size for validation (default: 100000)")
    parser.add_argument("--max-map-size", type=int, default=100000, dest="max_map_size",
                        help="Maximum allowed map size for validation (default: 100000)")
    parser.add_argument("--max-string-length", type=int, default=10000000, dest="max_string_length",
                        help="Maximum allowed string length for validation (default: 10000000)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    
    args = parser.parse_args()
    
    # Mutual exclusion check
    if args.no_msgpack and args.no_json:
        print("Error: Cannot use both --no-msgpack and --no-json together.")
        print("       At least one serialization format must be enabled.")
        sys.exit(1)
    
    # Default to all if nothing specified
    if not (args.dart or args.python or args.java or args.typescript or 
            args.rust or args.go or args.cpp or args.csharp or args.php or args.all):
        args.all = True
    
    # Load configuration
    config = load_config(args.config)
    
    # Get serialization options from config (can be overridden by CLI flags)
    global_config = config.get("config", {}).get("global", {})
    serialization = global_config.get("serialization", {})
    
    # Get type field name (used to identify packet type in serialized data)
    type_field = global_config.get("type_field", "packetType")

    # Config file settings (defaults to both enabled)
    config_no_msgpack = not serialization.get("msgpack", True)
    config_no_json = not serialization.get("json", True)

    # CLI flags override config file
    no_msgpack = args.no_msgpack or config_no_msgpack
    no_json = args.no_json or config_no_json

    # Check mutual exclusion after merging config and CLI
    if no_msgpack and no_json:
        print("Error: Cannot disable both MessagePack and JSON serialization.")
        print("       At least one serialization format must be enabled.")
        print("       Check both CLI flags and config.global.serialization in packets.json")
        sys.exit(1)

    # Parse packet definitions
    packets = []
    for path, definition in config.get("packets", {}).items():
        packet = PacketDefinition(path, definition)
        # Validate that no field uses the reserved type_field name
        for field in packet.fields:
            if field.name == type_field:
                print(f"Error: Field name '{type_field}' is reserved for packet type identification.")
                print(f"       Packet: {packet.name}")
                print(f"       Either rename your field or change config.global.type_field to a different name.")
                sys.exit(1)
        packets.append(packet)

    if not packets:
        print("Warning: No packets defined in config file")
        return

    print(f"Found {len(packets)} packet definition(s)")

    if no_msgpack:
        print("MessagePack support disabled - generating JSON-only code")

    if no_json:
        print("JSON support disabled - generating MessagePack-only code")

    # Get generator configs
    gen_config = config.get("config", {})

    # Generate for each platform
    if args.dart or args.all:
        dart_gen = DartGenerator(gen_config.get("dart", {}))
        dart_gen.generate(packets, args.override, args.clean, no_msgpack, no_json, type_field)

    if args.python or args.all:
        python_gen = PythonGenerator(gen_config.get("python", {}))
        python_gen.generate(packets, args.override, args.clean, no_msgpack, no_json, type_field)

    if args.java or args.all:
        java_gen = JavaGenerator(gen_config.get("java", {}))
        java_gen.generate(packets, args.override, args.clean, no_msgpack, no_json, type_field)

    if args.typescript or args.all:
        ts_gen = TypeScriptGenerator(gen_config.get("typescript", {}))
        ts_gen.generate(packets, args.override, args.clean, no_msgpack, no_json, type_field)

    if args.rust or args.all:
        rust_gen = RustGenerator(gen_config.get("rust", {}))
        rust_gen.generate(packets, args.override, args.clean, no_msgpack, no_json, type_field)

    if args.go or args.all:
        go_gen = GoGenerator(gen_config.get("go", {}))
        go_gen.generate(packets, args.override, args.clean, no_msgpack, no_json, type_field)

    if args.cpp or args.all:
        cpp_gen = CppGenerator(gen_config.get("cpp", {}))
        cpp_gen.generate(packets, args.override, args.clean, no_msgpack, no_json, type_field)

    if args.csharp or args.all:
        csharp_gen = CSharpGenerator(gen_config.get("csharp", {}))
        csharp_gen.generate(packets, args.override, args.clean, no_msgpack, no_json, type_field)

    if args.php or args.all:
        php_gen = PhpGenerator(gen_config.get("php", {}))
        php_gen.generate(packets, args.override, args.clean, no_msgpack, no_json, type_field)

    print("\nGeneration complete!")


if __name__ == "__main__":
    main()

