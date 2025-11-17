from openai import OpenAI

contract_data = """
{
  "contract": "DFS",
  "solidity_version": "0.4.x",
  "nodes": {
    "dfg_node_1": {
      "id": "dfg_node_1",
      "type": "contract",
      "name": "DFS",
      "data_type": null,
      "scope": "global",
      "source_location": {
        "line": 2,
        "column": 1,
        "end_line": 125,
        "end_column": 2
      },
      "properties": {
        "source_location": {
          "line": 2,
          "column": 1
        }
      }
    },
    "dfg_node_2": {
      "id": "dfg_node_2",
      "type": "state_variable",
      "name": "numDeposits",
      "data_type": "uint",
      "scope": "DFS",
      "source_location": {
        "line": 11,
        "column": 5,
        "end_line": 11,
        "end_column": 22
      },
      "properties": {
        "source_location": {
          "line": 11,
          "column": 5
        }
      }
    },
    "dfg_node_3": {
      "id": "dfg_node_3",
      "type": "state_variable",
      "name": "deposits",
      "data_type": "mapping (uint => Deposit)",
      "scope": "DFS",
      "source_location": {
        "line": 12,
        "column": 5,
        "end_line": 12,
        "end_column": 40
      },
      "properties": {
        "source_location": {
          "line": 12,
          "column": 5
        }
      }
    },
    "dfg_node_4": {
      "id": "dfg_node_4",
      "type": "state_variable",
      "name": "owner1",
      "data_type": "address",
      "scope": "DFS",
      "source_location": {
        "line": 14,
        "column": 5,
        "end_line": 14,
        "end_column": 74
      },
      "properties": {
        "source_location": {
          "line": 14,
          "column": 5
        }
      }
    },
    "dfg_node_5": {
      "id": "dfg_node_5",
      "type": "state_variable",
      "name": "owner2",
      "data_type": "address",
      "scope": "DFS",
      "source_location": {
        "line": 15,
        "column": 5,
        "end_line": 15,
        "end_column": 74
      },
      "properties": {
        "source_location": {
          "line": 15,
          "column": 5
        }
      }
    },
    "dfg_node_6": {
      "id": "dfg_node_6",
      "type": "function",
      "name": "makeDeposit",
      "data_type": null,
      "scope": "DFS",
      "source_location": {
        "line": 17,
        "column": 5,
        "end_line": 75,
        "end_column": 6
      },
      "properties": {
        "source_location": {
          "line": 17,
          "column": 5
        }
      }
    },
    "dfg_node_7": {
      "id": "dfg_node_7",
      "type": "state_variable",
      "name": "i",
      "data_type": "uint",
      "scope": "DFS",
      "source_location": {
        "line": 77,
        "column": 5,
        "end_line": 77,
        "end_column": 12
      },
      "properties": {
        "source_location": {
          "line": 77,
          "column": 5
        }
      }
    },
    "dfg_node_8": {
      "id": "dfg_node_8",
      "type": "function",
      "name": "pay",
      "data_type": null,
      "scope": "DFS",
      "source_location": {
        "line": 79,
        "column": 5,
        "end_line": 124,
        "end_column": 6
      },
      "properties": {
        "source_location": {
          "line": 79,
          "column": 5
        }
      }
    }
  },
  "edges": {
    "dfg_edge_1": {
      "id": "dfg_edge_1",
      "source": "dfg_node_1",
      "target": "dfg_node_2",
      "type": "definition",
      "label": null,
      "weight": 1,
      "properties": {}
    },
    "dfg_edge_2": {
      "id": "dfg_edge_2",
      "source": "dfg_node_1",
      "target": "dfg_node_3",
      "type": "definition",
      "label": null,
      "weight": 1,
      "properties": {}
    },
    "dfg_edge_3": {
      "id": "dfg_edge_3",
      "source": "dfg_node_1",
      "target": "dfg_node_4",
      "type": "definition",
      "label": null,
      "weight": 1,
      "properties": {}
    },
    "dfg_edge_4": {
      "id": "dfg_edge_4",
      "source": "dfg_node_1",
      "target": "dfg_node_5",
      "type": "definition",
      "label": null,
      "weight": 1,
      "properties": {}
    },
    "dfg_edge_5": {
      "id": "dfg_edge_5",
      "source": "dfg_node_1",
      "target": "dfg_node_6",
      "type": "definition",
      "label": null,
      "weight": 1,
      "properties": {}
    },
    "dfg_edge_6": {
      "id": "dfg_edge_6",
      "source": "dfg_node_1",
      "target": "dfg_node_7",
      "type": "definition",
      "label": null,
      "weight": 1,
      "properties": {}
    },
    "dfg_edge_7": {
      "id": "dfg_edge_7",
      "source": "dfg_node_1",
      "target": "dfg_node_8",
      "type": "definition",
      "label": null,
      "weight": 1,
      "properties": {}
    }
  },
  "metadata": {
    "generated_at": "2025-11-02T15:26:20.984804",
    "node_count": 8,
    "edge_count": 7,
    "serializer_version": "1.0.0",
    "edge_type_distribution": {
      "definition": 7
    },
    "node_type_distribution": {
      "contract": 1,
      "state_variable": 5,
      "function": 2
    }
  }
}
"""


client = OpenAI(
    api_key="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", 
    base_url="https://openrouter.ai/api/v1", 
)

response = client.chat.completions.create(
    model="openai/gpt-4.1-mini",
    timeout=60,
    messages=[
        {
            "role": "user",
            "content": """你是一名区块链智能合约风险审计专家，分析庞氏骗局、资金盘及高风险投资合约。

目标：准确分类风险。输入为结构化JSON格式数据流图。

请严格按照以下结构，仅输出JSON格式，不包含其他任何文字内容，JSON结构如下：
```json
{
    "is_ponzi": true/false,
    "confidence": 0~1,
    "risk_level": "高" | "中" | "低",
    "reasoning": ""
}
```

请分析以下智能合约数据：\n ```json{contract_data}```
""",
        }
    ]
)

print(response.choices[0].message.content)
