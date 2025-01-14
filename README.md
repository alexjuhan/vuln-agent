# Web Application LLM Vulnerability Agent

## Project Idea

LLM-powered code vulnerability triage

## Why

Currently, it’s difficult for software developers to test web applications for security vulnerabilities. Traditional tools flood developers with false positives. They often fail to provide findings that consider a software application’s specific threat model.
We are building LLM security agents to enhance traditional web application testing with agentic reasoning. These agents build on open source tools to detect and prioritize vulnerabilities in software applications. Our tool will display a dashboard of the top vulnerabilities with detailed analysis connected to CVEs and OWASP.

Static Application Security Testing (SAST) and Software Composition Analysis (SCA) tools identify known vulnerabilities in source code, but their findings are not contextualized and require manual triage by engineers and analysts. 
Using LLMs’ contextual awareness and reasoning, we can analyze the tools’ findings and prioritize exploitable vulnerabilities. We’ll load the source code into a vector database to allow the agents to search it, coming up with their own hypothesis about vulnerabilities in the source code.

MITRE’s Common Weakness Scoring System (CWSS) documentation describes the problem well: “Software developers often face hundreds or thousands of individual bug reports for weaknesses that are discovered in their code. In certain circumstances, a software weakness can even lead to an exploitable vulnerability. Due to this high volume of reported weaknesses, stakeholders are often forced to prioritize which issues they should investigate and fix first, often using incomplete information. In short, people need to be able to reason and communicate about the relative importance of different weaknesses.”

The OWASP Web Security Testing Guide further describes the problem: “Static source code analysis alone cannot identify issues due to flaws in the design, since it cannot understand the context in which the code is constructed. Source code analysis tools are useful in determining security issues due to coding errors, however, significant manual effort is required to validate the findings.”

## What

It displays a dashboard with the top vulnerabilities and security recommendations for a project, connected to CVE and OWASP data.
It uses LLM agents with Static Application Security Testing (SAST) and Software Composition Analysis (SCA) to triage and prioritize vulnerabilities.

## When

Throughout software development and QA

## Where

The app could run locally with docker-compose, in CI/CD pipelines, or as a hosted offering.

## Who

Software developers, Product security teams, open source maintainers

## How

We plan to use various open source SAST/SCA tools such as CodeQL, semgrep, OWASP Dependency Check, npm audit, PyPi Safety, and others.

We will use an LLM agent framework such as huggingface/smolagents for code execution and tool calling. We’ll structure the various SAST/SCA as Tools which the agent can invoke.




