import os
import calendar
from datetime import date, datetime
from supabase import create_client, Client

import altair as alt
import pandas as pd
import streamlit as st


DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "health_log.csv")

COLUMN_NAMES_RU = {
    "date": "Дата",
    "time": "Время",
    "systolic": "Верхнее давление",
    "diastolic": "Нижнее давление",
    "pulse": "Пульс",
    "oxygen": "Кислород SpO₂",
    "feeling": "Самочувствие",
    "comment": "Комментарий",
}

APP_COLUMNS = [
    "id",
    "date",
    "time",
    "systolic",
    "diastolic",
    "pulse",
    "oxygen",
    "feeling",
    "comment",
]

MONTH_NAMES_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


def ensure_data_file():
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(
            columns=[
                "date",
                "time",
                "systolic",
                "diastolic",
                "pulse",
                "oxygen",
                "feeling",
                "comment",
            ]
        )
        df.to_csv(DATA_FILE, index=False)


def load_data():
    supabase = get_supabase_client()

    response = (
        supabase.table("health_records")
        .select("*")
        .order("record_date", desc=True)
        .order("record_time", desc=True)
        .execute()
    )

    records = response.data

    if not records:
        return pd.DataFrame(columns=APP_COLUMNS)

    df = pd.DataFrame(records)

    df = df.rename(
        columns={
            "record_date": "date",
            "record_time": "time",
        }
    )

    df = df[
        [
            "id",
            "date",
            "time",
            "systolic",
            "diastolic",
            "pulse",
            "oxygen",
            "feeling",
            "comment",
        ]
    ]

    numeric_columns = ["systolic", "diastolic", "pulse", "oxygen"]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def save_record(record):
    supabase = get_supabase_client()

    supabase_record = {
        "record_date": record["date"],
        "record_time": record["time"],
        "systolic": record["systolic"],
        "diastolic": record["diastolic"],
        "pulse": record["pulse"],
        "oxygen": record["oxygen"],
        "feeling": record["feeling"],
        "comment": record["comment"],
    }

    supabase.table("health_records").insert(supabase_record).execute()

def delete_last_record():
    supabase = get_supabase_client()

    response = (
        supabase.table("health_records")
        .select("id")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return False

    latest_record_id = response.data[0]["id"]

    supabase.table("health_records").delete().eq("id", int(latest_record_id)).execute()

    return True

def update_record(record_id, updated_record):
    supabase = get_supabase_client()

    supabase_record = {
        "record_date": updated_record["date"],
        "record_time": updated_record["time"],
        "systolic": updated_record["systolic"],
        "diastolic": updated_record["diastolic"],
        "pulse": updated_record["pulse"],
        "oxygen": updated_record["oxygen"],
        "feeling": updated_record["feeling"],
        "comment": updated_record["comment"],
    }

    supabase.table("health_records").update(supabase_record).eq("id", int(record_id)).execute()

    return True

def value_or_default(value, default):
    if pd.isna(value):
        return default
    return int(value)

def render_health_card(label, value, note=None):
    note_html = f'<div class="health-card-note">{note}</div>' if note else ""

    st.markdown(
        f"""
        <div class="health-card">
            <div class="health-card-label">{label}</div>
            <div class="health-card-value">{value}</div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

def format_average(value):
    if pd.isna(value):
        return "Нет данных"
    return round(value, 1)

def get_current_time_without_seconds():
    return datetime.now().time().replace(second=0, microsecond=0)

def format_display_value(value):
    if pd.isna(value):
        return "Не измерено"

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)

def get_supabase_client():
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]

    return create_client(supabase_url, supabase_key)

def parse_time_value(value):
    time_text = str(value)

    try:
        return datetime.strptime(time_text, "%H:%M").time()
    except ValueError:
        return datetime.strptime(time_text, "%H:%M:%S").time()

st.set_page_config(
    page_title="Дневник здоровья",
    page_icon="❤️",
    layout="wide",
)

st.title("❤️ Дневник здоровья")
with st.expander("Проверка подключения к Supabase"):
    try:
        supabase = get_supabase_client()
        response = supabase.table("health_records").select("id").limit(1).execute()
        st.success("Supabase подключён. Таблица health_records доступна.")
    except Exception as error:
        st.error("Не удалось подключиться к Supabase.")
        st.code(str(error))
st.caption("Личный дневник давления, пульса, кислорода и самочувствия.")

st.markdown(
    """
    <style>
    .health-card {
        background-color: #f7f8fa;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 10px;
    }

    .health-card-label {
        font-size: 16px;
        color: #6b7280;
        margin-bottom: 8px;
    }

    .health-card-value {
        font-size: 22px;
        font-weight: 600;
        color: #2f3340;
        line-height: 1.2;
    }

    .health-card-note {
        font-size: 14px;
        color: #6b7280;
        margin-top: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

tab_add, tab_history, tab_stats = st.tabs(
    ["➕ Добавить запись", "📋 История", "📊 Статистика"]
)
with tab_add:
    st.subheader("Добавить новую запись")

    if "add_form_counter" not in st.session_state:
        st.session_state["add_form_counter"] = 0

    form_counter = st.session_state["add_form_counter"]

    with st.form(f"health_form_{form_counter}"):
        col1, col2 = st.columns(2)

        with col1:
            today = date.today()

            month_names = [
                "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
            ]

            col_day, col_month, col_year = st.columns(3)

            with col_day:
                day = st.number_input(
                    "День",
                    min_value=1,
                    max_value=31,
                    value=today.day,
                    key=f"add_day_{form_counter}",
                )

            with col_month:
                month = st.selectbox(
                    "Месяц",
                    options=list(range(1, 13)),
                    format_func=lambda x: MONTH_NAMES_RU[x - 1],
                    index=today.month - 1,
                    key=f"add_month_{form_counter}",
                )

            with col_year:
                year = st.number_input(
                    "Год",
                    min_value=2020,
                    max_value=2100,
                    value=today.year,
                    key=f"add_year_{form_counter}",
                )

            days_in_month = calendar.monthrange(year, month)[1]

            if day > days_in_month:
                st.warning(f"В выбранном месяце только {days_in_month} дней. Дата будет исправлена.")
                day = days_in_month

            record_date = date(year, month, day)

            record_time = st.time_input(
                "Время",
                value=get_current_time_without_seconds(),
                key=f"add_time_{form_counter}",
            )

            pressure_not_measured = st.checkbox(
                "Давление не измерено",
                key=f"add_pressure_not_measured_{form_counter}",
            )

            if pressure_not_measured:
                systolic = None
                diastolic = None
                st.info("Давление будет сохранено как «не измерено».")
            else:
                systolic = st.number_input(
                "Верхнее давление",
                min_value=50,
                max_value=250,
                value=120,
                key=f"add_systolic_{form_counter}",
                )

                diastolic = st.number_input(
                    "Нижнее давление",
                    min_value=30,
                    max_value=160,
                    value=80,
                    key=f"add_diastolic_{form_counter}",
                )

        with col2:
            pulse_not_measured = st.checkbox(
                "Пульс не измерен",
                key=f"add_pulse_not_measured_{form_counter}",
            )

            if pulse_not_measured:
                pulse = None
                st.info("Пульс будет сохранён как «не измерено».")
            else:
                pulse = st.number_input(
                    "Пульс",
                    min_value=30,
                    max_value=220,
                    value=70,
                    key=f"add_pulse_{form_counter}",
                )

            oxygen_not_measured = st.checkbox(
                "Кислород не измерен",
                key=f"add_oxygen_not_measured_{form_counter}",
            )

            if oxygen_not_measured:
                oxygen = None
                st.info("Кислород будет сохранён как «не измерено».")
            else:
                oxygen = st.number_input(
                    "Кислород SpO₂ (%)",
                    min_value=50,
                    max_value=100,
                    value=98,
                    key=f"add_oxygen_{form_counter}",
                )
            
            feeling = st.selectbox(
                "Самочувствие",
                ["Хорошее", "Нормальное", "Плохое"],
                key=f"add_feeling_{form_counter}",
            )

            comment = st.text_area(
                "Комментарий",
                placeholder="Например: болела голова, после прогулки, после таблеток...",
                key=f"add_comment_{form_counter}",
            )

        submitted = st.form_submit_button("Сохранить запись")

        if submitted:
            record = {
                "date": record_date.strftime("%Y-%m-%d"),
                "time": record_time.strftime("%H:%M"),
                "systolic": systolic,
                "diastolic": diastolic,
                "pulse": pulse,
                "oxygen": oxygen,
                "feeling": feeling,
                "comment": comment,
            }

            save_record(record)

            st.session_state["add_form_counter"] += 1
            st.success("Запись сохранена!")
            st.rerun()

with tab_history:
    st.subheader("История записей")

    df = load_data()

    if df.empty:
        st.info("Пока записей нет.")
    else:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["datetime"] = pd.to_datetime(df["date"].dt.strftime("%Y-%m-%d") + " " + df["time"].astype(str))
        df = df.sort_values("datetime", ascending=False)

        latest_record = df.iloc[0]

        st.subheader("Последняя запись")

        col1, col2, col3, col4 = st.columns(4)

        pressure_text = (
            "Не измерено"
            if pd.isna(latest_record["systolic"]) or pd.isna(latest_record["diastolic"])
            else f"{int(latest_record['systolic'])}/{int(latest_record['diastolic'])}"
        )

        pulse_text = (
            "Не измерено"
            if pd.isna(latest_record["pulse"])
            else int(latest_record["pulse"])
        )

        oxygen_text = (
            "Не измерено"
            if pd.isna(latest_record["oxygen"])
            else f"{int(latest_record['oxygen'])}%"
        )

        with col1:
            render_health_card("Давление", pressure_text)

        with col2:
            render_health_card("Пульс", pulse_text)

        with col3:
            render_health_card("Кислород SpO₂", oxygen_text)

        with col4:
            render_health_card("Самочувствие", latest_record["feeling"])

        latest_date_text = latest_record["datetime"].strftime("%d.%m.%Y %H:%M")
        st.caption(f"Дата и время последней записи: {latest_date_text}")

        if pd.notna(latest_record["comment"]) and str(latest_record["comment"]).strip():
            st.info(f"Комментарий: {latest_record['comment']}")

        st.divider()

        st.subheader("Записи за выбранный месяц")

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            history_year = st.selectbox(
                "Год",
                sorted(df["date"].dt.year.unique(), reverse=True),
                key="history_year",
            )

        with filter_col2:
            history_months = sorted(
                df[df["date"].dt.year == history_year]["date"].dt.month.unique()
            )

            history_month = st.selectbox(
                "Месяц",
                history_months,
                format_func=lambda x: MONTH_NAMES_RU[x - 1],
                key="history_month",
            )

        filtered_df = df[
            (df["date"].dt.year == history_year)
            & (df["date"].dt.month == history_month)
        ].copy()

        filtered_df = filtered_df.drop(columns=["datetime"], errors="ignore")

        display_df = filtered_df.copy()

        display_df = display_df.drop(columns=["id"], errors="ignore")
        display_df["date"] = pd.to_datetime(display_df["date"]).dt.strftime("%d.%m.%Y")

        numeric_columns = ["systolic", "diastolic", "pulse", "oxygen"]

        for column in numeric_columns:
            display_df[column] = display_df[column].apply(format_display_value)

        display_df["feeling"] = display_df["feeling"].fillna("Нормальное")
        display_df["comment"] = display_df["comment"].fillna("")

        display_df = display_df.rename(columns=COLUMN_NAMES_RU)

        st.dataframe(display_df, width="stretch", hide_index=True)

        csv_data = display_df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="⬇️ Скачать резервную копию за выбранный месяц",
            data=csv_data,
            file_name=f"health_diary_{history_year}_{history_month:02d}.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("✏️ Редактировать запись")

        edit_df = df.copy()
        edit_df["datetime"] = pd.to_datetime(
            edit_df["date"].astype(str) + " " + edit_df["time"].astype(str)
        )
        edit_df = edit_df.sort_values("datetime", ascending=False)

        record_options = {}

        for row_index, row in edit_df.iterrows():
            label = (
                f"{row['datetime'].strftime('%d.%m.%Y %H:%M')} — "
                f"{row['systolic'] if pd.notna(row['systolic']) else 'не измерено'}/"
                f"{row['diastolic'] if pd.notna(row['diastolic']) else 'не измерено'}, "
                f"пульс: {row['pulse'] if pd.notna(row['pulse']) else 'не измерен'}, "
                f"SpO₂: {row['oxygen'] if pd.notna(row['oxygen']) else 'не измерен'}, "
                f"{row['feeling']}"
            )
            record_options[label] = row["id"]

        selected_label = st.selectbox(
            "Выберите запись для редактирования",
            list(record_options.keys()),
        )

        selected_record_id = record_options[selected_label]
        selected_record = df[df["id"] == selected_record_id].iloc[0]

        with st.form("edit_record_form"):
            st.write("Изменить выбранную запись")

            edit_date = pd.to_datetime(selected_record["date"]).date()

            edit_time_value = parse_time_value(selected_record["time"])

            col_edit1, col_edit2 = st.columns(2)

            with col_edit1:
                edit_year = edit_date.year
                edit_month = edit_date.month
                edit_day = edit_date.day

                col_edit_day, col_edit_month, col_edit_year = st.columns(3)

                with col_edit_day:
                    new_day = st.number_input(
                        "День",
                        min_value=1,
                        max_value=31,
                        value=edit_day,
                        key=f"edit_day_{selected_record_id}",
                    )

                with col_edit_month:
                    new_month = st.selectbox(
                        "Месяц",
                        options=list(range(1, 13)),
                        format_func=lambda x: MONTH_NAMES_RU[x - 1],
                        index=edit_month - 1,
                        key=f"edit_month_{selected_record_id}",
                    )

                with col_edit_year:
                    new_year = st.number_input(
                        "Год",
                        min_value=2020,
                        max_value=2100,
                        value=edit_year,
                        key=f"edit_year_{selected_record_id}",
                    )

                days_in_new_month = calendar.monthrange(new_year, new_month)[1]

                if new_day > days_in_new_month:
                    st.warning(f"В выбранном месяце только {days_in_new_month} дней. Дата будет исправлена.")
                    new_day = days_in_new_month

                new_date = date(new_year, new_month, new_day)

                new_time = st.time_input(
                    "Время",
                    value=edit_time_value,
                    key=f"edit_time_{selected_record_id}",
                )

                pressure_not_measured_edit = st.checkbox(
                    "Давление не измерено",
                    value=pd.isna(selected_record["systolic"]) and pd.isna(selected_record["diastolic"]),
                    key=f"edit_pressure_not_measured_{selected_record_id}",
                )

                if pressure_not_measured_edit:
                    new_systolic = None
                    new_diastolic = None
                else:
                    new_systolic = st.number_input(
                        "Верхнее давление",
                        min_value=50,
                        max_value=250,
                        value=value_or_default(selected_record["systolic"], 120),
                        key=f"edit_systolic_{selected_record_id}",
                    )

                    new_diastolic = st.number_input(
                        "Нижнее давление",
                        min_value=30,
                        max_value=160,
                        value=value_or_default(selected_record["diastolic"], 80),
                        key=f"edit_diastolic_{selected_record_id}",
                    )

            with col_edit2:
                pulse_not_measured_edit = st.checkbox(
                    "Пульс не измерен",
                    value=pd.isna(selected_record["pulse"]),
                    key=f"edit_pulse_not_measured_{selected_record_id}",
                )

                if pulse_not_measured_edit:
                    new_pulse = None
                else:
                    new_pulse = st.number_input(
                        "Пульс",
                        min_value=30,
                        max_value=220,
                        value=value_or_default(selected_record["pulse"], 70),
                        key=f"edit_pulse_{selected_record_id}",
                    )

                oxygen_not_measured_edit = st.checkbox(
                    "Кислород не измерен",
                    value=pd.isna(selected_record["oxygen"]),
                    key=f"edit_oxygen_not_measured_{selected_record_id}",
                )

                if oxygen_not_measured_edit:
                    new_oxygen = None
                else:
                    new_oxygen = st.number_input(
                        "Кислород SpO₂ (%)",
                        min_value=50,
                        max_value=100,
                        value=value_or_default(selected_record["oxygen"], 98),
                        key=f"edit_oxygen_{selected_record_id}",
                    )

                new_feeling = st.selectbox(
                    "Самочувствие",
                    ["Хорошее", "Нормальное", "Плохое"],
                    index=["Хорошее", "Нормальное", "Плохое"].index(selected_record["feeling"]),
                    key=f"edit_feeling_{selected_record_id}",
                )

                comment_value = selected_record.get("comment", "")

                if pd.isna(comment_value):
                    comment_value = ""
                else:
                    comment_value = str(comment_value)

                comment_key = f"edit_comment_{selected_record_id}_{len(comment_value)}"

                new_comment = st.text_area(
                    "Комментарий",
                    value=comment_value,
                    key=comment_key,
                )

            save_changes = st.form_submit_button("💾 Сохранить изменения")

            if save_changes:
                updated_record = {
                    "date": new_date.strftime("%Y-%m-%d"),
                    "time": new_time.strftime("%H:%M"),
                    "systolic": new_systolic,
                    "diastolic": new_diastolic,
                    "pulse": new_pulse,
                    "oxygen": new_oxygen,
                    "feeling": new_feeling,
                    "comment": new_comment,
                }

                updated = update_record(selected_record_id, updated_record)

                if updated:
                    st.success("Запись обновлена.")
                    st.rerun()
                else:
                    st.error("Не удалось обновить запись.")

        st.divider()

        st.warning("Удаление записи нельзя отменить.")

        confirm_delete = st.checkbox("Я понимаю, что последняя добавленная запись будет удалена")

        if st.button("🗑️ Удалить последнюю добавленную запись"):
            if confirm_delete:
                deleted = delete_last_record()

                if deleted:
                    st.success("Последняя добавленная запись удалена.")
                    st.rerun()
                else:
                    st.info("Удалять нечего.")
            else:
                st.error("Сначала подтвердите удаление.")

with tab_stats:
    st.subheader("Статистика")

    df = load_data()

    if df.empty:
        st.info("Пока недостаточно данных для статистики.")
    else:
        df["date"] = pd.to_datetime(df["date"])

        col1, col2 = st.columns(2)

        with col1:
            selected_year = st.selectbox(
                "Год",
                sorted(df["date"].dt.year.unique(), reverse=True),
            )

        with col2:
                available_months = sorted(
                    df[df["date"].dt.year == selected_year]["date"].dt.month.unique()
                )

                selected_month = st.selectbox(
                    "Месяц",
                    available_months,
                    format_func=lambda x: MONTH_NAMES_RU[x - 1],
                )

        month_df = df[
            (df["date"].dt.year == selected_year)
            & (df["date"].dt.month == selected_month)
        ]

        if month_df.empty:
            st.info("За выбранный месяц записей нет.")
        else:
            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Среднее верхнее", format_average(month_df["systolic"].mean()))
            col2.metric("Среднее нижнее", format_average(month_df["diastolic"].mean()))
            col3.metric("Средний пульс", format_average(month_df["pulse"].mean()))
            col4.metric("Средний SpO₂", format_average(month_df["oxygen"].mean()))

            bad_days = (month_df["feeling"] == "Плохое").sum()
            st.metric("Записей с плохим самочувствием", bad_days)

            st.write("### Давление по датам")

            chart_df = month_df.copy()

            chart_df["datetime"] = pd.to_datetime(
                chart_df["date"].dt.strftime("%Y-%m-%d") + " " + chart_df["time"].astype(str)
            )

            chart_df = chart_df.sort_values("datetime")

            pressure_df = chart_df[["datetime", "systolic", "diastolic"]].rename(
                columns={
                    "datetime": "Дата и время",
                    "systolic": "Верхнее давление",
                    "diastolic": "Нижнее давление",
                }
            )

            pressure_df = pressure_df.dropna(
                subset=["Верхнее давление", "Нижнее давление"],
                how="all",
            )

            pressure_long = pressure_df.melt(
                id_vars="Дата и время",
                var_name="Показатель",
                value_name="Значение",
            )

            base_pressure = alt.Chart(pressure_long).encode(
                x=alt.X(
                    "Дата и время:T",
                    title=None,
                    axis=alt.Axis(
                        format="%d.%m %H:%M",
                        labelFontSize=11,
                        labelAngle=0,
                    ),
                ),
                y=alt.Y(
                    "Значение:Q",
                    title="Давление",
                ),
                color=alt.Color(
                    "Показатель:N",
                    title=None,
                ),
            )

            pressure_line = base_pressure.mark_line()

            pressure_points = base_pressure.mark_circle(size=90).encode(
                tooltip=[
                    alt.Tooltip("Дата и время:T", title="Дата и время", format="%d.%m.%Y %H:%M"),
                    alt.Tooltip("Показатель:N", title="Показатель"),
                    alt.Tooltip("Значение:Q", title="Значение"),
                ]
            )

            pressure_chart = (pressure_line + pressure_points).properties(
                height=400,
                padding={"bottom": 70}
            )

            st.altair_chart(pressure_chart, width="stretch")

            st.write("### Пульс")

            pulse_df = chart_df[["datetime", "pulse"]].rename(
                columns={
                    "datetime": "Дата и время",
                    "pulse": "Пульс",
                }
            )

            pulse_df = pulse_df.dropna(subset=["Пульс"])

            pulse_chart = (
                alt.Chart(pulse_df)
                .mark_line(point=alt.OverlayMarkDef(size=80))
                .encode(
                    x=alt.X(
                        "Дата и время:T",
                        title=None,
                        axis=alt.Axis(format="%d.%m %H:%M"),
                    ),
                    y=alt.Y(
                        "Пульс:Q",
                        title="Пульс",
                    ),
                    tooltip=[
                        alt.Tooltip("Дата и время:T", title="Дата и время", format="%d.%m.%Y %H:%M"),
                        alt.Tooltip("Пульс:Q", title="Пульс"),
                    ],
                )
                .properties(height=350)
            )

            st.altair_chart(pulse_chart, width="stretch")


            st.write("### Кислород SpO₂")

            oxygen_df = chart_df[["datetime", "oxygen"]].rename(
                columns={
                    "datetime": "Дата и время",
                    "oxygen": "Кислород SpO₂",
                }
            )

            oxygen_df = oxygen_df.dropna(subset=["Кислород SpO₂"])

            oxygen_chart = (
                alt.Chart(oxygen_df)
                .mark_line(point=alt.OverlayMarkDef(size=80))
                .encode(
                    x=alt.X(
                        "Дата и время:T",
                            title=None,
                            axis=alt.Axis(format="%d.%m %H:%M"),
                        ),
                    y=alt.Y(
                        "Кислород SpO₂:Q",
                        title="Кислород SpO₂",
                    ),
                    tooltip=[
                        alt.Tooltip("Дата и время:T", title="Дата и время", format="%d.%m.%Y %H:%M"),
                        alt.Tooltip("Кислород SpO₂:Q", title="Кислород SpO₂"),
                    ],
                )
                .properties(height=350)
            )

            st.altair_chart(oxygen_chart, width="stretch")

st.divider()
st.caption("Приложение предназначено только для личного ведения дневника и не заменяет консультацию врача.")