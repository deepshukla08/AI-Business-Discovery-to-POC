"""Runnable check for the merger and the graph wiring: python test_pipeline.py

Free. The merger has no model call at all, and the graph check stubs the model out —
this proves the plumbing, not the prompts.
"""

from langgraph.types import Command

from app.agents import llm
from app.schemas.discovery import (
    Brief,
    Chunk,
    Cited,
    Feature,
    Finding,
    Gap,
    Outline,
    ProposedStep,
    Redesign,
    Role,
    Screen,
)


def finding(kind, text, cites, source):
    return Finding(type=kind, text=text, cites=cites, source_id=source)


def check_merger():
    from app.agents.merger import merge

    findings = [
        # the same problem, described differently, in three separate files
        finding("pain", "Ravi assigns orders to drivers over the phone every morning",
                ["a_1"], "call_1.txt"),
        finding("pain", "Drivers phone Ravi each morning to be told their assignments",
                ["b_2"], "call_2.txt"),
        finding("pain", "Every morning assignment happens by phone call with Ravi",
                ["c_3"], "whatsapp.txt"),
        # same subject, different type — must NOT merge
        finding("requirement", "Drivers should see their own assignments without calling",
                ["a_9"], "call_1.txt"),
        # unrelated
        finding("pain", "Proof of delivery photos are deleted weekly for storage",
                ["a_4"], "call_1.txt"),
    ]

    insights = merge(findings)

    assert len(insights) == 3, [i.text for i in insights]

    top = insights[0]
    assert len(top.sources) == 3, top.sources
    assert sorted(top.cites) == ["a_1", "b_2", "c_3"], top.cites
    assert top.type == "pain"

    # corroboration ranks first
    assert [len(i.sources) for i in insights] == [3, 1, 1]
    # a requirement never folds into a pain, however similar the words
    assert any(i.type == "requirement" for i in insights)
    # nothing is lost
    assert sum(len(i.cites) for i in insights) == 5

    print(f"merger      5 findings -> {len(insights)} insights, top backed by {len(top.sources)} sources")


def check_graph_wiring():
    """Every node runs, in order, and state accumulates. Model stubbed."""
    calls = []

    def stub(prompt, schema, **kwargs):
        calls.append(kwargs.get("thinking"))
        if schema is Brief:
            return Brief(
                goal=Cited(text="Stop running dispatch through one phone", cites=["s_000"]),
                current_process=[Cited(text="Orders arrive by email", cites=["s_000"])],
                pain_points=[Cited(text="Assignments live in one head", cites=["s_000"])],
                requirements=[Cited(text="Daily CSV by 8pm", cites=["s_000"])],
                constraints=[Cited(text="Drivers have old phones", cites=["s_000"])],
                stated_wants=[Cited(text="A customer tracking app", cites=["s_000"])],
            )
        if schema == list[Gap]:  # `is` fails: each list[Gap] is a fresh generic alias
            return [
                Gap(kind="unanswered", question="How many orders per day?",
                    why_it_matters="Sizing and price depend on it", cites=["s_000"]),
                Gap(kind="never_discussed", question="Who approves refunds?",
                    why_it_matters="Blocks the approval flow", cites=[]),
                Gap(kind="contradiction", question="Which is true?",
                    why_it_matters="Design differs", cites=["made_up_id"]),
            ]
        if schema is Redesign:
            return Redesign(
                summary="Put the status somewhere other than one person's phone",
                to_be=[
                    ProposedStep(step="Orders land on a board", change="new",
                                 why="Removes retyping", cites=["s_000"]),
                    ProposedStep(step="Invented step", change="new",
                                 why="cites nothing, must survive", cites=["ghost_id"]),
                ],
                wins=[Cited(text="Double assignment becomes impossible", cites=["s_000"])],
                not_solved=[Cited(text="Address quality", cites=["ghost_id"])],
            )
        if schema is Outline:
            return Outline(
                app_name="Dispatch Board",
                one_liner="One place where every order's status lives",
                roles=[Role(name="Dispatcher", does="Assigns orders")],
                features=[Feature(name="Assign", solves="Double assignment", priority="must")],
                screens=[Screen(name="Board", role="Dispatcher", purpose="Assign work",
                                elements=["columns", "assign button"])],
                flow=["Order arrives", "Dispatcher assigns", "Driver delivers"],
            )
        # extractor
        source = prompt.split("`")[1]
        return [Finding(type="pain", text=f"pain from {source}", cites=[f"{source[:3]}_000"])]

    # the prototyper returns a file, not a record, so it uses the text path
    def stub_text(prompt, **kwargs):
        calls.append(kwargs.get("thinking"))
        return "```html\n<!DOCTYPE html><html><body><script>let x=1</script>" + "x" * 900 + "</body></html>\n```"

    from app.graph.pipeline import pipeline

    original = llm.generate_json
    original_text = llm.generate_text
    llm.generate_json = stub
    llm.generate_text = stub_text
    try:

        chunks = [
            Chunk(id="src_000", source_id="src.txt", locator="1", text="one"),
            Chunk(id="oth_000", source_id="oth.txt", locator="1", text="two"),
            Chunk(id="s_000", source_id="src.txt", locator="2", text="three"),
        ]
        # every run needs a thread now that the graph is checkpointed
        config = {"configurable": {"thread_id": "wiring-check"}}
        pipeline.invoke({"project_id": "check", "chunks": chunks, "findings": []}, config)
        # the graph stops at ask_client; this check is about the nodes, so wave it through
        # with no answers — which is itself a valid choice a consultant can make
        state = pipeline.invoke(Command(resume=[]), config)
    finally:
        llm.generate_json = original
        llm.generate_text = original_text
        pipeline.checkpointer.delete_thread("wiring-check")

    assert len(state["findings"]) == 2, "one extractor per source"
    assert state["insights"], "merge produced nothing"
    assert state["brief"].goal.text.startswith("Stop running"), state["brief"].goal
    assert len(state["gaps"]) == 2, (
        "the contradiction citing a fake chunk id should have been dropped, "
        f"and never_discussed kept: {[g.kind for g in state['gaps']]}"
    )
    assert {g.kind for g in state["gaps"]} == {"unanswered", "never_discussed"}

    # a proposed step may be genuinely new and cite nothing, so it survives...
    assert len(state["redesign"].to_be) == 2, state["redesign"].to_be
    assert state["redesign"].to_be[1].cites == [], "invented citation should be stripped"
    # ...but a claim about what the change does or does not fix must point at evidence
    assert state["redesign"].not_solved == [], "uncited not_solved should be dropped"
    assert state["outline"].app_name == "Dispatch Board"

    # the ``` fence models add despite being told not to must be stripped
    assert state["prototype"].startswith("<!DOCTYPE html>"), state["prototype"][:40]
    assert state["prototype_faults"] == [], state["prototype_faults"]

    # per-agent thinking levels actually reach the model layer
    assert "LOW" in calls and "MEDIUM" in calls and "HIGH" in calls, calls

    nodes = [n for n in pipeline.get_graph().nodes if not n.startswith("__")]
    print(
        f"graph       {len(nodes)} nodes wired, {len(calls)} model calls, "
        f"thinking levels {sorted(set(calls))}"
    )


def check_human_in_the_loop():
    """The graph must stop before designing anything, and carry the answers forward."""
    from langgraph.types import Command

    from app.graph.pipeline import pipeline, unfinished

    thread = "hitl-check"
    config = {"configurable": {"thread_id": thread}}
    seen_answers = []

    def stub(prompt, schema, **kwargs):
        if schema == list[Finding]:
            return [Finding(type="pain", text="phones ring all night", cites=["src_000"])]
        if schema is Brief:
            return Brief(
                goal=Cited(text="Stop the phone ringing", cites=["src_000"]),
                current_process=[], pain_points=[], requirements=[],
                constraints=[], stated_wants=[],
            )
        if schema == list[Gap]:
            return [Gap(kind="unanswered", question="How many orders per day?",
                        why_it_matters="Sizing", cites=["src_000"])]
        if schema is Redesign:
            # the proposal must be able to see what the client came back with
            seen_answers.append("A: 250 on a normal Monday" in prompt)
            return Redesign(summary="s", to_be=[], wins=[], not_solved=[])
        return Outline(app_name="X", one_liner="y", roles=[], features=[], screens=[], flow=[])

    original, original_text = llm.generate_json, llm.generate_text
    llm.generate_json = stub
    llm.generate_text = lambda p, **k: "<html><body><script>1</script>" + "x" * 900 + "</body></html>"
    try:
        chunks = [Chunk(id="src_000", source_id="src.txt", locator="1", text="one")]
        for _ in pipeline.stream({"project_id": thread, "chunks": chunks, "findings": []}, config):
            pass

        # it stopped, and stopped in the right place — before anything was designed
        assert unfinished(thread) == ("ask_client",), unfinished(thread)
        paused = pipeline.get_state(config).values
        assert paused.get("brief"), "the brief should exist before the pause"
        assert "redesign" not in paused, "nothing may be designed before the human answers"

        for _ in pipeline.stream(
            Command(resume=[{"question": "How many orders per day?", "answer": "250 on a normal Monday"}]),
            config,
        ):
            pass

        done = pipeline.get_state(config).values
        assert unfinished(thread) == (), unfinished(thread)
        assert [a.answer for a in done["answers"]] == ["250 on a normal Monday"]
        assert done.get("redesign"), "the run did not continue past the pause"
        assert seen_answers == [True], "the redesigner never saw the client's answer"

        print("human loop  paused before designing, resumed with the answer in the prompt")
    finally:
        llm.generate_json, llm.generate_text = original, original_text
        pipeline.checkpointer.delete_thread(thread)


def check_resume():
    """A run killed halfway must resume, not repay the calls it already made."""
    from app.agents import merger
    from app.graph.pipeline import pipeline, unfinished

    thread = "resume-check"
    config = {"configurable": {"thread_id": thread}}
    extractions = []

    def stub(prompt, schema, **kwargs):
        if schema == list[Finding]:
            source = prompt.split("`")[1]
            extractions.append(source)
            return [Finding(type="pain", text=f"from {source}", cites=[f"{source[:3]}_000"])]
        raise RuntimeError("synthesizer exploded")  # dies after extract + merge

    original = llm.generate_json
    llm.generate_json = stub
    try:
        chunks = [
            Chunk(id="src_000", source_id="src.txt", locator="1", text="one"),
            Chunk(id="oth_000", source_id="oth.txt", locator="1", text="two"),
        ]
        try:
            pipeline.invoke({"project_id": thread, "chunks": chunks, "findings": []}, config)
            raise AssertionError("the stub should have failed the run")
        except RuntimeError:
            pass

        assert len(extractions) == 2, extractions
        assert unfinished(thread) == ("synthesize",), unfinished(thread)

        # resume: extract and merge must NOT run again
        state = pipeline.get_state(config).values
        assert len(state["findings"]) == 2, "findings from before the crash were lost"
        assert state["insights"], "merge output was lost"
        assert len(extractions) == 2, "resume re-ran the extractors"

        print(f"resume      crashed after merge; {len(extractions)} extract calls, not repeated")
    finally:
        llm.generate_json = original
        # this check writes to the same store the app uses; leave nothing behind
        pipeline.checkpointer.delete_thread(thread)


if __name__ == "__main__":
    check_merger()
    check_graph_wiring()
    check_human_in_the_loop()
    check_resume()
    print("\npipeline ok (no quota spent)")
