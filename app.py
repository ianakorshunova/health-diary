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

def import_backup_to_supabase(uploaded_file):
    try:
        backup_df = pd.read_csv(uploaded_file)
    except Exception:
        return False, "Не удалось прочитать CSV-файл."

    reverse_column_names = {
        "Дата": "date",
        "Время": "time",
        "Верхнее давление": "systolic",
        "Нижнее давление": "diastolic",
        "Пульс": "pulse",
        "Кислород SpO₂": "oxygen",
        "Самочувствие": "feeling",
        "Комментарий": "comment",
    }

    backup_df = backup_df.rename(columns=reverse_column_names)

    required_columns = [
        "date",
        "time",
        "systolic",
        "diastolic",
        "pulse",
        "oxygen",
        "feeling",
        "comment",
    ]

    missing_columns = [column for column in required_columns if column not in backup_df.columns]

    if missing_columns:
        return False, f"В файле не хватает колонок: {', '.join(missing_columns)}"

    backup_df = backup_df[required_columns].copy()
    backup_df = backup_df.replace("Не измерено", pd.NA)

    backup_df["date"] = pd.to_datetime(
        backup_df["date"],
        errors="coerce",
        dayfirst=True,
    )

    if backup_df["date"].isna().any():
        return False, "В файле есть строки с некорректной датой."

    backup_df["date"] = backup_df["date"].dt.strftime("%Y-%m-%d")
    backup_df["time"] = backup_df["time"].astype(str).str.slice(0, 5)

    numeric_columns = ["systolic", "diastolic", "pulse", "oxygen"]

    for column in numeric_columns:
        backup_df[column] = pd.to_numeric(backup_df[column], errors="coerce")

    backup_df["feeling"] = backup_df["feeling"].fillna("Нормальное")
    backup_df["comment"] = backup_df["comment"].fillna("")

    # records_to_insert = []

    # for _, row in backup_df.iterrows():
    #     record = {
    #         "record_date": row["date"],
    #         "record_time": row["time"],
    #         "systolic": None if pd.isna(row["systolic"]) else int(row["systolic"]),
    #         "diastolic": None if pd.isna(row["diastolic"]) else int(row["diastolic"]),
    #         "pulse": None if pd.isna(row["pulse"]) else int(row["pulse"]),
    #         "oxygen": None if pd.isna(row["oxygen"]) else int(row["oxygen"]),
    #         "feeling": row["feeling"],
    #         "comment": row["comment"],
    #     }

    #     records_to_insert.append(record)

    # if not records_to_insert:
    #     return False, "В файле нет записей для импорта."

    # supabase = get_supabase_client()
    # supabase.table("health_records").insert(records_to_insert).execute()

    # return True, f"Импортировано записей: {len(records_to_insert)}."

    def normalize_time_for_key(value):
        return str(value)[:5]


    def normalize_optional_int(value):
        if pd.isna(value):
            return None

        return int(value)


    def normalize_text(value):
        if pd.isna(value):
            return ""

        return str(value).strip()


    existing_df = load_data()
    existing_keys = set()

    for _, existing_row in existing_df.iterrows():
        existing_key = (
            str(existing_row["date"]),
            normalize_time_for_key(existing_row["time"]),
            normalize_optional_int(existing_row["systolic"]),
            normalize_optional_int(existing_row["diastolic"]),
            normalize_optional_int(existing_row["pulse"]),
            normalize_optional_int(existing_row["oxygen"]),
            normalize_text(existing_row["feeling"]),
            normalize_text(existing_row["comment"]),
        )

        existing_keys.add(existing_key)


    records_to_insert = []
    skipped_duplicates = 0

    for _, row in backup_df.iterrows():
        record_key = (
            row["date"],
            normalize_time_for_key(row["time"]),
            normalize_optional_int(row["systolic"]),
            normalize_optional_int(row["diastolic"]),
            normalize_optional_int(row["pulse"]),
            normalize_optional_int(row["oxygen"]),
            normalize_text(row["feeling"]),
            normalize_text(row["comment"]),
        )

        if record_key in existing_keys:
            skipped_duplicates += 1
            continue

        record = {
            "record_date": row["date"],
            "record_time": normalize_time_for_key(row["time"]),
            "systolic": record_key[2],
            "diastolic": record_key[3],
            "pulse": record_key[4],
            "oxygen": record_key[5],
            "feeling": record_key[6],
            "comment": record_key[7],
        }

        records_to_insert.append(record)
        existing_keys.add(record_key)


    if not records_to_insert:
        if skipped_duplicates > 0:
            return True, f"Новых записей нет. Пропущено дублей: {skipped_duplicates}."

        return False, "В файле нет записей для импорта."


    supabase = get_supabase_client()
    supabase.table("health_records").insert(records_to_insert).execute()

    return True, (
        f"Импортировано записей: {len(records_to_insert)}. "
        f"Пропущено дублей: {skipped_duplicates}."
    )

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

        st.subheader("⬆️ Импортировать записи из CSV")

        st.info(
            "Импорт добавит записи из CSV в базу Supabase. "
            "Текущие записи не будут удалены."
        )

        uploaded_backup = st.file_uploader(
            "Выберите CSV-файл",
            type=["csv"],
        )

        import_confirmed = st.checkbox(
            "Я понимаю, что записи из файла будут добавлены в дневник"
        )

        if "import_message" in st.session_state:
            if st.session_state.get("import_success"):
                st.success(st.session_state["import_message"])
            else:
                st.error(st.session_state["import_message"])

            del st.session_state["import_message"]
            del st.session_state["import_success"]


        if st.button("Импортировать записи"):
            if uploaded_backup is None:
                st.error("Сначала выберите CSV-файл.")
            elif not import_confirmed:
                st.error("Сначала подтвердите импорт.")
            else:
                imported, message = import_backup_to_supabase(uploaded_backup)

                st.session_state["import_message"] = message
                st.session_state["import_success"] = imported

                st.rerun()

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